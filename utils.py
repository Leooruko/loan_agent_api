from langchain_community.llms.ollama import Ollama
from langchain.tools import Tool, tool
from langchain.agents import initialize_agent, AgentExecutor, AgentType
from langchain.memory import ConversationBufferMemory
from pandasql import sqldf
import pandas as pd
import re 
import traceback
import asyncio
import logging
from config import AI_CONFIG, DATA_CONFIG, ERROR_MESSAGES, SUCCESS_MESSAGES

# Configure logging
logger = logging.getLogger(__name__)

# Initialize conversation memory
conversation_memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    input_key="input"
)

# Initialize LLM with improved system prompt
llm = Ollama(
    model=AI_CONFIG['MODEL_NAME'],
    system='''
You are a helpful AI assistant for loan data analysis. Your job is to answer questions about loan portfolios, payments, and clients.

IMPORTANT RULES:
1. ALWAYS use the fetch_data tool for ANY question about loan data
2. Write simple SQL queries using the 'df' table
3. Keep responses clear and helpful
4. If asked about non-loan topics, politely redirect to loan questions
5. Remember previous conversation context and build on it
6. If user refers to previous results, use that context in your response

AVAILABLE DATA (table 'df'):
- Managed_By: Loan manager name
- Loan_No: Unique loan identifier  
- Loan_Product_Type: Type of loan product
- Client_Code: Unique client identifier
- Client_Name: Client's name
- Issued_Date: When loan was issued
- Amount_Disbursed: Loan amount given to client
- Installments: Total number of installments
- Total Paid: Amount client has paid so far (use backticks: `Total Paid`)
- Total Charged: Total amount owed (principal + interest) (use backticks: `Total Charged`)
- Days_Since_Issued: Days since loan was issued
- Is_Installment_Day: Whether today is a payment day
- Weeks_Passed: Weeks since loan was issued
- Installments_Expected: Expected payments by now
- Installment_Amount: Amount per payment
- Expected_Paid_Today: Expected payment for today
- Expected_Before_Today: Expected total payments by now
- Arrears: Unpaid amount
- Due_Today: Amount due today
- Mobile_Phone_No: Client's phone number
- Status: Loan status (Active, Closed, etc.)
- Client_Loan_Count: Total loans client has had
- Client_Type: Individual or Group loan

IMPORTANT: Column names with spaces must be enclosed in backticks (`) in SQL queries.

RESPONSE FORMAT:
For loan data questions:
1. Use fetch_data tool with SQL query
2. Analyze the results
3. Provide clear, helpful answer
4. Reference previous conversation if relevant

For non-loan questions:
"I'm here to help with loan and financial data questions. Could you ask me something about your loan portfolio, payments, or clients instead?"

EXAMPLE QUERIES:
- "How many active loans?" → SELECT COUNT(*) FROM df WHERE Status = 'Active'
- "Total portfolio value?" → SELECT SUM(Amount_Disbursed) FROM df WHERE Status = 'Active'
- "Clients with high arrears?" → SELECT Client_Name, Arrears FROM df WHERE Arrears > 0 ORDER BY Arrears DESC LIMIT 10
- "Total payments by manager?" → SELECT Managed_By, SUM(`Total Paid`) FROM df GROUP BY Managed_By ORDER BY SUM(`Total Paid`) DESC
'''
)

@tool
def fetch_data(query):
    '''
    Executes SQL queries on loan data to help answer user questions about loans, payments, and clients.

    Args:
        query (str): SQL query to execute on the loan dataset

    Returns: 
        str: Query results as formatted string or error message
    '''
    try:
        # Validate input
        if not isinstance(query, str) or not query.strip():
            return "Error: Please provide a valid SQL query."
        
        # Clean and validate query
        query = query.strip().strip("`").strip("'").strip('"')
        
        # Security check - only allow SELECT queries
        if not re.search(r'^SELECT\s+', query, re.IGNORECASE):
            return "Error: Only SELECT queries are allowed for security reasons."
        
        # Check for basic SQL structure
        if not re.search(r'SELECT\s+.*\s+FROM\s+df', query, re.IGNORECASE):
            return "Error: Query must select from the 'df' table."
        
        # Limit query complexity for safety
        if len(query) > AI_CONFIG['MAX_SQL_LENGTH']:
            return "Error: Query is too complex. Please simplify your question."
        
        # Load data
        try:
            df = pd.read_csv(DATA_CONFIG['CSV_FILE_PATH'])
            logger.info(f"Data loaded successfully. Shape: {df.shape}")
        except FileNotFoundError:
            logger.error("Data file not found")
            return ERROR_MESSAGES['NO_DATA']
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return "Error: Unable to load loan data. Please try again later."
        
        # Execute query
        logger.info(f"Executing query: {query}")
        result = sqldf(query)
        
        # Handle empty results
        if result.empty:
            return "No data found matching your query. Try rephrasing your question."
        
        # Format result as string
        if len(result) <= 10:
            # For small results, show full data
            return f"Query Results:\n{result.to_string(index=False)}"
        else:
            # For large results, show summary
            return f"Query Results (showing first 10 of {len(result)} rows):\n{result.head(10).to_string(index=False)}"

    except Exception as e:
        logger.error(f"Error in fetch_data: {e}")
        error_msg = str(e).lower()
        
        if "syntax" in error_msg or "invalid" in error_msg:
            return "Error: Invalid SQL syntax. Please rephrase your question."
        elif "table" in error_msg or "column" in error_msg:
            return "Error: Invalid table or column name. Please check your query."
        elif "timeout" in error_msg:
            return "Error: Query took too long. Please try a simpler question."
        else:
            return f"Error: Unable to process query. Please try again."

# Create tools list
tools = [
    Tool(
        name="fetch_data",
        func=fetch_data,
        description="Use this tool to query loan data. Input should be a SQL SELECT statement using the 'df' table. Note: Column names with spaces must be enclosed in backticks (e.g., `Total Paid`, `Total Charged`)."
    )
]

# Create agent executor with memory
try:
    # Use agent initialization with memory
    agent_executor = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,  # Use conversational agent for memory
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=4,
        memory=conversation_memory
    )
except Exception as e:
    logger.error(f"Agent initialization failed: {e}")
    # Create a basic agent as fallback
    agent_executor = None

async def promt_llm(query, conversation_history=None):
    """
    Process user query and return AI response with improved error handling and memory.
    """
    try:
        # Validate input
        if not query or not query.strip():
            return SUCCESS_MESSAGES['WELCOME']
        
        # Check if query is too long
        if len(query) > AI_CONFIG['MAX_QUERY_LENGTH']:
            return ERROR_MESSAGES['COMPLEX_QUERY']
        
        # Log the request
        logger.info(f"Processing query: {query[:100]}...")
        
        # Check if agent is available
        if agent_executor is None:
            return "I'm having trouble initializing the AI system. Please restart the application."
        
        # Use agent_executor with timeout
        try:
            response = agent_executor.invoke({"input": query})
            result = response.get("output", "No response generated")
            
            # Clean up the response
            if isinstance(result, str):
                # Remove any tool call artifacts
                result = re.sub(r'Action:.*?Action Input:.*?Observation:.*?', '', result, flags=re.DOTALL)
                result = result.strip()
                
                # If response is too short or seems like an error, provide a helpful message
                if len(result) < 10 or "error" in result.lower():
                    return "I'm having trouble understanding that question. Could you please ask about loans, payments, or clients in a different way?"
                
                return result
            else:
                return "I'm here to help with loan and financial data questions. What would you like to know about your loan portfolio?"
                
        except Exception as agent_error:
            logger.error(f"Agent execution error: {agent_error}")
            return ERROR_MESSAGES['GENERAL_ERROR']
            
    except Exception as e:
        logger.error(f'Error processing query: {e}')
        traceback.print_exc()
        
        # Provide user-friendly error messages
        error_msg = str(e).lower()
        if "timeout" in error_msg or "connection" in error_msg:
            return ERROR_MESSAGES['TIMEOUT']
        elif "memory" in error_msg or "resource" in error_msg:
            return ERROR_MESSAGES['RESOURCE_ERROR']
        else:
            return ERROR_MESSAGES['GENERAL_ERROR']

def clear_conversation_memory():
    """Clear the conversation memory"""
    try:
        # Reset conversation memory
        global conversation_memory, agent_executor
        conversation_memory.clear()
        
        # Recreate the agent executor with fresh memory
        agent_executor = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=4,
            memory=conversation_memory
        )
        return "Conversation memory cleared successfully."
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        return "Memory cleared (with some issues)."

def get_conversation_memory():
    """Get the current conversation memory"""
    try:
        if hasattr(conversation_memory, 'chat_memory'):
            return conversation_memory.chat_memory.messages
        else:
            return []
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        return []

async def main():
    """Main function for testing the LLM interaction"""
    print("Loan Assistant - Type 'exit' to quit")
    print("=" * 50)
    
    while True:
        try:
            query = input("\nAsk about your loan data: ")
            if query.lower() in ["exit", "quit"]:
                break
                
            if not query.strip():
                continue
                
            print("\nProcessing...")
            response = await promt_llm(query)
            print(f"\nAssistant: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
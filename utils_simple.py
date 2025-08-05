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
You are an AI assistant for Greencom Solutions Ltd, specialized in data analytics and mathematical reasoning. You are working with a processed dataset of loan clients and payments, including payment schedules and statuses.

    Your tasks include:
    - Understanding user queries, particularly those involving trends, anomalies, financial health, or optimization.
    - Using mathematical reasoning (including proportional logic, ratios, expected value, deviation, etc.) to hypothesize and interpret results.
    - Formulating SQL queries in DuckDB style using the table `df`.
    - Using the `fetch_data` tool to get data.
    - Analyzing and explaining results clearly, including any logical or mathematical insights.
    - Recommending actions or observations based on patterns or hypothesis tests.

    Workflow:
    1. Interpret the user’s question and determine what data and logic are needed.
    2. Formulate a valid SQL query over the `df` table.
    3. Use the `fetch_data` tool with the query string as input.
    4. Use mathematical or logical reasoning to evaluate the result.
    5. Provide a clear answer and, if relevant, offer hypotheses, explanations, or recommendations.

    Response format:
    If a tool is needed, follow this format:
    Thought: ...
    Action: fetch_data
    Action Input: SELECT ... FROM df WHERE ...

    If no tool is needed, just respond with:
    Answer: ...

    Important Notes:
    
    - The SQL query must be a plain string (no backticks or quotes).
    - Use the `fetch_data` tool only for data-related questions.
    - If the question is not about the dataset, reply: "Sorry, the dataset does not contain information about that topic."
    - Where applicable, apply concepts like:
    - Deviation from expected behavior
    - Ratio and proportionality (e.g., total paid vs expected)
    - Prediction and estimation
    - Group-based behavior comparison
    - Time-based trends (e.g., weekly payment changes)
    - Format DataFrame results clearly (Markdown-friendly tables). No inline JSON or object-like responses.

    Dataset Columns:
    - Managed_By: Loan manager
    - Loan_No: Unique loan ID
    - Loan_Product_Type: Product type (e.g. "BIASHARA4W")
    - Client_Code: Unique client ID
    - Client_Name: Name of client
    - Issued_Date: Date loan was issued
    - Amount_Disbursed: Disbursed loan amount
    - Installments: Number of installments
    - Total Paid: Total paid by client
    - Total Charged: Total owed (principal + interest)
    - Days_Since_Issued: Days since loan was issued
    - Is_Installment_Day: Whether today is an installment day
    - Weeks_Passed: Weeks since issue
    - Installments_Expected: Expected installments by now
    - Installment_Amount: Expected amount per installment
    - Expected_Paid_Today: Expected payment for today
    - Expected_Before_Today: Expected cumulative payment
    - Arrears: Unpaid amount
    - Due_Today: Amount due today
    - Mobile_Phone_No: Client’s phone
    - Status: Loan status ("Active", "Closed", etc.)
    - Client_Loan_Count: Total loans the client has had
    - Client_Type: "Individual" or "Group"
   
    IMPORTANT: Column names with spaces must be enclosed in backticks (`) in SQL queries.

    EXAMPLE QUERIES:
    - "How many active loans?" → SELECT COUNT(*) FROM df WHERE Status = 'Active'
    - "Total portfolio value?" → SELECT SUM(Amount_Disbursed) FROM df WHERE Status = 'Active'
    - "Clients with high arrears?" → SELECT Client_Name, Arrears FROM df WHERE Arrears > 0 ORDER BY Arrears DESC LIMIT 10
    - "Total payments by manager?" → SELECT Managed_By, SUM(`Total Paid`) FROM df GROUP BY Managed_By ORDER BY SUM(`Total Paid`) DESC
    '''
)

@tool
def fetch_data(query: str):
    """
    Fetches data from a processed dataset using DuckDB-style SQL.
    """
    try:
        if not isinstance(query, str) or query.strip() == "":
            return "Error: Query must be a non-empty string."

        # Remove triple backticks or quotes
        query = query.strip().strip("`").strip("'").strip('"')

        # Attempt to extract the SQL part only
        match = re.search(r'(SELECT .*?FROM .*?)(?:;|\n|$)', query, re.IGNORECASE | re.DOTALL)
        if match:
            query = match.group(1).strip()
        else:
            return "Error: Could not parse a valid SQL query."

        print("Executing SQL query:", query)

        df = pd.read_csv("processed_data.csv")
        print("Executing: ",query)
        result = sqldf(query)
        return result
    except Exception as e:
        return f"Error: {e}"

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
        max_iterations=AI_CONFIG['MAX_ITERATIONS'],
        memory=conversation_memory
    )
except Exception as e:
    logger.error(f"Agent initialization failed: {e}")
    # Create a basic agent as fallback
    agent_executor = None

async def promt_llm(query, conversation_history=None):
    """
    Process user query and return AI response.
    """
    try:
        if agent_executor is None:
            return "I'm having trouble initializing the AI system. Please restart the application."
        
        response = agent_executor.invoke({"input": query})
        result = response.get("output", "No response generated")
        
        if isinstance(result, str):
            # Remove any tool call artifacts
            result = re.sub(r'Action:.*?Action Input:.*?Observation:.*?', '', result, flags=re.DOTALL)
            result = result.strip()
            return result
        else:
            return "I'm here to help with loan and financial data questions. What would you like to know about your loan portfolio?"
                
    except Exception as e:
        return "I'm having trouble processing your request. Please try again."

def clear_conversation_memory():
    """Clear the conversation memory"""
    try:
        global conversation_memory, agent_executor
        conversation_memory.clear()
        
        agent_executor = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=AI_CONFIG['MAX_ITERATIONS'],
            memory=conversation_memory
        )
        return "Conversation memory cleared successfully."
    except Exception as e:
        return "Memory cleared (with some issues)."

def get_conversation_memory():
    """Get the current conversation memory"""
    try:
        if hasattr(conversation_memory, 'chat_memory'):
            return conversation_memory.chat_memory.messages
        else:
            return []
    except Exception as e:
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
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
You are a friendly and enthusiastic loan data analyst at BrightCom loans, with a passion for creative HTML and CSS coding. You love making data beautiful and engaging! Query the loan dataset and provide answers in stunning HTML format.

FORMAT:
Thought: [reasoning]
Action: fetch_data
Action Input: [SQL query]
Final Answer: [Beautiful HTML response]

RULES:
- Use fetch_data tool to query the df table
- Use backticks for column names with spaces: `Total Paid`, `Total Charged`
- Be creative with your HTML responses - use colors, icons, cards, and modern styling
- Always be friendly and enthusiastic in your responses
- Key columns: 
    - Managed_By (manager) - The name of the manager who is responsible for the loan
    - Loan_No (loan ID) - The unique identifier for the loan
    - Client_Code (client ID) - The unique identifier for the client
    - Client_Name - The name of the client
    - Total Paid - The total amount paid by the client
    - Total Charged - The total amount charged by the client
    - Status - The status of the loan
    - Arrears - The amount of arrears for the loan
    - Loan_Product_Type - The type of loan product i.e (BIASHARA4W,BIASHARA6W,INUKA6WKS,INUKA4WKS,INUKA8WKS)
    - Issued_Date - The date the loan was issued
    - Amount_Disbursed - The amount of money disbursed to the client
    - Installments - The number of installments for the loan
    - Days_Since_Issued - The number of days since the loan was issued
    - Is_Installment_Day - Whether today is an installment day for the loan
    - Weeks_Passed - The number of weeks passed since the loan was issued
    - Installments_Expected - The number of installments to be completed by today
    - Installment_Amount - The amount of money paid per installment
    - Expected_Paid - The amount of money expected to be paid by today
    - Expected_Before_Today - The amount of money expected to be paid before today
    - Due_Today - The amount of money due today if today is an installment day
    - Mobile_Phone_No - The mobile phone number of the client
    - Status - The status of the loan
    - Client_Loan_Count - The number of loans the client has
    - Client_Type - The type of client i.e (New, Repeat)

- Final Answer must be beautiful HTML only, no backticks or markdown
- Wrap response in: <div class="response-container">...</div>
- Use modern CSS classes like: .success-card, .info-card, .warning-card, .data-table, .highlight, .metric
- Add emojis and friendly language to make responses engaging

EXAMPLE:
Thought: I need to find the top performing manager by total payments
Action: fetch_data
Action Input: SELECT Managed_By, SUM(`Total Paid`) FROM df GROUP BY Managed_By ORDER BY SUM(`Total Paid`) DESC LIMIT 1
Final Answer: <div class="response-container"><div class="success-card"><h3>🏆 Top Performing Manager</h3><p>🎉 <strong>John Doe</strong> is absolutely crushing it as our top performer with <span class="highlight">KES 1,256,417</span> in total payments! What an amazing achievement! 🌟</p></div></div>

EXAMPLE 2:
Thought: I need to find the manager with the most loans
Action: fetch_data
Action Input: SELECT Managed_By, COUNT(Loan_No) FROM df GROUP BY Managed_By ORDER BY COUNT(Loan_No) DESC LIMIT 1
Final Answer: <div class="response-container"><div class="info-card"><h3>📊 Manager with Most Loans</h3><p>💼 <strong>John Doe</strong> is managing an impressive portfolio of <span class="metric">150 loans</span> - that's some serious dedication to our clients! 👏</p></div></div>

EXAMPLE 3:
Thought: I need to find clients with arrears
Action: fetch_data
Action Input: SELECT COUNT(*) as Total_Clients, SUM(`Total Charged` - `Total Paid`) as Total_Arrears FROM df WHERE Arrears > 0
Final Answer: <div class="response-container"><div class="warning-card"><h3>⚠️ Arrears Alert</h3><p>We have <span class="metric">{Total_Clients}</span> clients with outstanding arrears totaling <span class="highlight">KES {Total_Arrears:,.2f}</span>. Let's reach out and help them get back on track! 🤝</p></div></div>
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
        
        # Return plain text result for the agent to process
        if not result.empty:
            return result.to_string(index=False)
        else:
            return "No data found matching your query."
            
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
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,  # More flexible format
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=AI_CONFIG['MAX_ITERATIONS'],  # More iterations for complex queries
    memory=conversation_memory
)


async def promt_llm(query, conversation_history=None):
    """
    Process user query and return AI response.
    """
    try:
        if agent is None:
            return "I'm having trouble initializing the AI system. Please restart the application."
        
        response = agent.invoke({"input": query})
        result = response.get("output", "No response generated")
        
        if isinstance(result, str):
            # Look for "Final Answer:" and extract everything after it
            final_answer_match = re.search(r'Final Answer:\s*(.*)', result, re.DOTALL)
            if final_answer_match:
                result = final_answer_match.group(1).strip()
                # Remove any markdown formatting (backticks, code blocks)
                result = re.sub(r'^```.*?\n', '', result, flags=re.DOTALL)
                result = re.sub(r'\n```$', '', result, flags=re.DOTALL)
                result = re.sub(r'^`|`$', '', result)
                result = re.sub(r'```.*?```', '', result, flags=re.DOTALL)
                result = re.sub(r'^`|`$', '', result)
                # Remove any text before the first HTML tag
                html_start = result.find('<')
                if html_start > 0:
                    result = result[html_start:]
                # Remove any text after the last HTML tag
                html_end = result.rfind('>')
                if html_end > 0:
                    result = result[:html_end + 1]
            else:
                # If no "Final Answer:" found, try to extract any HTML content
                html_start = result.find('<')
                if html_start >= 0:
                    result = result[html_start:]
                    html_end = result.rfind('>')
                    if html_end > 0:
                        result = result[:html_end + 1]
                else:
                    # Try to find any HTML-like content in the response
                    html_pattern = re.search(r'<div[^>]*>.*?</div>', result, re.DOTALL)
                    if html_pattern:
                        result = html_pattern.group(0)
                    else:
                        # Fallback: create a simple HTML response
                        result = f'<div class="response-container"><p class="answer-text">I found some data: {result.strip()}</p></div>'
            
            print(result)
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
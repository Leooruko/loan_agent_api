from langchain_community.llms.ollama import Ollama
from langchain.tools import Tool,tool
from langchain.agents import initialize_agent,AgentExecutor,AgentType
from pandasql import sqldf
import pandas as pd
import re 
import traceback
import asyncio
from config import AI_CONFIG, DATA_CONFIG, ERROR_MESSAGES, SUCCESS_MESSAGES

llm = Ollama(
    model = AI_CONFIG['MODEL_NAME'],
    system='''
    You are a friendly and helpful AI assistant for Brightcom, specializing in loan and financial data analysis. You help users understand their loan portfolio, payment trends, and financial insights.

    Your role is to:
    - Answer questions about loan data in a clear, conversational way
    - Provide helpful insights about payment patterns, client behavior, and financial trends
    - Use simple language and avoid technical jargon
    - Be patient and explain complex concepts in easy-to-understand terms

    When users ask questions:
    1. If it's about loan data, use the fetch_data tool to get information
    2. If it's not about loan data, politely redirect them to loan-related topics
    3. Always provide context and explanations for your answers
    4. Use friendly, encouraging language

    Available data includes:
    - Client information (names, phone numbers, loan counts)
    - Loan details (amounts, installments, due dates)
    - Payment status and arrears
    - Loan managers and product types
    - Payment schedules and expectations

    To query data, use:
    Action: fetch_data
    Action Input: SELECT [columns] FROM df WHERE [conditions]

    Important guidelines:
    - Only query the 'df' table
    - Keep SQL queries simple and focused
    - If a question isn't about loan data, say: "I'm here to help with loan and financial data questions. Could you ask me something about your loan portfolio, payments, or clients instead?"
    - Always provide helpful context with your answers
    - Use friendly, conversational language

    Example responses:
    "Based on the data, I can see that [insight]. This suggests [explanation]."
    "Let me check that for you... [data analysis]"
    "I'd be happy to help with loan-related questions! What would you like to know about your loan portfolio?"
    '''
)

@tool
def fetch_data(query):
    '''
    Executes SQL queries on loan data to help answer user questions about loans, payments, and clients.

    Args:
        query (str): SQL query to execute on the loan dataset

    Returns: 
        pandas.DataFrame: Query results or error message if query fails
        
    Available data columns:
    - Managed_By: Loan manager name
    - Loan_No: Unique loan identifier
    - Loan_Product_Type: Type of loan product
    - Client_Code: Unique client identifier
    - Client_Name: Client's name
    - Issued_Date: When loan was issued
    - Amount_Disbursed: Loan amount given to client
    - Installments: Total number of installments
    - Total_Paid: Amount client has paid so far
    - Total_Charged: Total amount owed (principal + interest)
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
    '''
    try:
        # Validate input
        if not isinstance(query, str) or query.strip() == "":
            return "I need a valid query to help you. Could you please rephrase your question?"
        
        # Clean and validate query
        query = query.strip().strip("`").strip("'").strip('"')
        
        # Check for basic SQL structure
        if not re.search(r'SELECT\s+.*\s+FROM\s+df', query, re.IGNORECASE):
            return "I can only help with questions about the loan data. Please ask about loans, payments, or clients."
        
        # Limit query complexity for safety
        if len(query) > AI_CONFIG['MAX_SQL_LENGTH']:
            return ERROR_MESSAGES['COMPLEX_QUERY']
        
        # Load data
        try:
            df = pd.read_csv(DATA_CONFIG['CSV_FILE_PATH'])
        except FileNotFoundError:
            return ERROR_MESSAGES['NO_DATA']
        
        # Execute query
        print(f"Executing query: {query}")
        result = sqldf(query)
        
        # Handle empty results
        if result.empty:
            return ERROR_MESSAGES['EMPTY_RESULTS']
        
        return result

    except Exception as e:
        error_msg = str(e).lower()
        if "syntax" in error_msg or "invalid" in error_msg:
            return ERROR_MESSAGES['INVALID_QUERY']
        elif "table" in error_msg or "column" in error_msg:
            return ERROR_MESSAGES['INVALID_QUERY']
        else:
            return ERROR_MESSAGES['GENERAL_ERROR']

tools = [
    Tool(name="fetch_data",func=fetch_data,description="Tool to query the only data to answer users questions")
]

# Create agent executor directly
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True
    ),
    tools=tools,
    handle_parsing_errors=True,
    verbose=True,
    max_iterations=3
)

async def promt_llm(query, conversation_history=None):
    try:
        # Validate input
        if not query or not query.strip():
            return SUCCESS_MESSAGES['WELCOME']
        
        # Check if query is too long
        if len(query) > AI_CONFIG['MAX_QUERY_LENGTH']:
            return ERROR_MESSAGES['COMPLEX_QUERY']
        
        # Use agent_executor
        response = agent_executor.invoke({"input": query})
        return response["output"]
    except Exception as e:
        print(f'Error processing query: {e}')
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
    # Temporarily disabled due to compatibility issues
    return "Memory feature temporarily disabled for compatibility."

def get_conversation_memory():
    """Get the current conversation memory"""
    # Temporarily disabled due to compatibility issues
    return []

async def main():
    while True:
        query = input("Ask about your data: ")
        if query.lower() in ["exit", "quit"]:
            break
        response = await promt_llm(query)
        print(response)

if __name__ == "__main__":
    asyncio.run(main()) 
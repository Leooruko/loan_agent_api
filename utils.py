from langchain_community.llms.ollama import Ollama
from langchain.tools import Tool,tool
from langchain.agents import initialize_agent,AgentExecutor,AgentType
from pandasql import sqldf
import pandas as pd
import re 
from langchain.memory import ConversationBufferMemory
import traceback
import asyncio
from config import AI_CONFIG, DATA_CONFIG, ERROR_MESSAGES, SUCCESS_MESSAGES

memory = ConversationBufferMemory(return_messages=True)

llm = Ollama(
    model = AI_CONFIG['MODEL_NAME'],
    system='''
    You are a friendly and helpful AI assistant for Brightcom, specialized in data analytics and mathematical reasoning. You are working with a processed dataset of loan clients and payments, including payment schedules and statuses.
    
    Your role is to:
    - Understanding user queries, particularly those involving trends, anomalies, financial health, or optimization.
    - Using mathematical reasoning (including proportional logic, ratios, expected value, deviation, etc.) to hypothesize and interpret results.
    - Formulating SQL queries in DuckDB style using the table `df`.
    - Using the `fetch_data` tool to get data.
    - Analyzing and explaining results clearly, including any logical or mathematical insights.
    - Recommending actions or observations based on patterns or hypothesis tests.
    - Answer questions about loan data in a clear, conversational way
    - Provide helpful insights about payment patterns, client behavior, and financial trends
    - Use simple language and avoid technical jargon
    - Be patient and explain complex concepts in easy-to-understand terms

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
 
    Important guidelines:
    - Only query the 'df' table
    - Keep SQL queries simple and focused
    - If a question isn't about loan data, say: "I'm here to help with loan and financial data questions. Could you ask me something about your loan portfolio, payments, or clients instead?"
    - Always provide helpful context with your answers
    - Use friendly, conversational language

    Dataset Columns:
    - Managed_By: Loan manager
    - Loan_No: Unique loan ID
    - Loan_Product_Type: Product type (e.g. "BIASHARA4W")
    - Client_Code: Unique client ID
    - Client_Name: Name of client
    - Issued_Date: Date loan was issued
    - Amount_Disbursed: Disbursed loan amount
    - Installments: Number of installments
    - Total_Paid: Total paid by client
    - Total_Charged: Total owed (principal + interest)
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

    Example tool use:
    Action: fetch_data  
    Action Input: SELECT Client_Name, Total_Paid, Expected_Before_Today FROM df WHERE Status = 'Active';

    Final Answer:  
    Client John Doe has paid KES 20,000, which is KES 5,000 below the expected KES 25,000. This suggests a shortfall, possibly due to missed installments.
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

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,    
    # max_iterations=1,
    memory=memory
)
agent_executor = AgentExecutor.from_agent_and_tools(agent,tools=tools,handle_parsing_errors=True,)



async def promt_llm(query):
    try:
        # Validate input
        if not query or not query.strip():
            return SUCCESS_MESSAGES['WELCOME']
        
        # Check if query is too long
        if len(query) > AI_CONFIG['MAX_QUERY_LENGTH']:
            return ERROR_MESSAGES['COMPLEX_QUERY']
        
        response = agent.invoke(query)
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

async def main():
    while True:
        query = input("Ask about your data: ")
        if query.lower() in ["exit", "quit"]:
            break
        response =await promt_llm(query)
        print(response)

if __name__ == "__main__":
    asyncio.run(main())
from langchain_community.llms.ollama import Ollama
from langchain.tools import Tool,tool
from langchain.agents import initialize_agent,AgentExecutor,AgentType
from pandasql import sqldf
import pandas as pd
import re 
from langchain.memory import ConversationBufferMemory
import traceback
import asyncio

memory = ConversationBufferMemory(return_messages=True)

llm = Ollama(
    model = "mistral",
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

    When using a tool, respond with:
    Action:\n fetch_data
    Action Input:\n SELECT ... FROM df WHERE ...

    After receiving the result, respond with:
    Final Answer:\n <your reasoning, insight, or table>

    Important Notes:
    - You can ONLY query the table named `df`. All SQL queries must begin with `SELECT ... FROM df`.
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

    The `df` table contains the following columns. Only use these columns in your queries:
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
    Executes a DuckDB-style SQL query on pandas DataFrame  loaded from 'processed_data.csv'

    This function is designed to be used by an agent  to retrieve data from a predefined CSV file .
    The agent should formulate  a SQL query as a string  and pass it  to this tool. 
    The table name within the query must be df


    Args:
        query: (str):A string containing  the SQL query to be executed.
                     The query should be in Duckdb style and refer to the dataframe as 'df'.

        Returns: 
            pandas.DataFrame: A dataframe  containing  the results of the query.
            str: An error message if the  query is invalid, the CSV is not found, or another exception occurs.
        
    The `df` table contains the following columns. Only use these columns in your queries:
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

    Example for Agent:
        Action: fetch_data
        Action Input: SELECT "Client_Name", "Total_Paid" FROM df WHERE "Status" = 'Active'
    
    '''
    try:
        if not isinstance(query, str) or query.strip() == "":
            return "Error: Query must be a non-empty string."
        query = query.strip().strip("`").strip("'").strip('"')
        match = re.search(r'(SELECT .*?FROM .*?)(?:;|\n|$)', query, re.IGNORECASE | re.DOTALL)
        if match:
            query = match.group(1).strip()
        else:
            return "Error: Could not parse a valid SQL query."
        
        df = pd.read_csv("processed_data.csv")
        print("Executing: ",query)
        result = sqldf(query)
        return result

    except Exception as e:
        return f"Error fetching data: {e}"   
    


tools = [
    Tool(name="fetch_data",func=fetch_data,description="Tool to query the only data to answer users questions")
]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,    
    max_iterations=1,
    memory=memory
)
agent_executor = AgentExecutor.from_agent_and_tools(agent,tools=tools,handle_parsing_errors=True,)



async def promt_llm(query):
    try:
        response = agent.invoke(query)
        return response["output"]
    except Exception as e:
        print(f'error as {e}')
        traceback.print_exc()
        return f"Error on promt: {e}"

async def main():
    while True:
        query = input("Ask about your data: ")
        if query.lower() in ["exit", "quit"]:
            break
        response =await promt_llm(query)
        print(response)

if __name__ == "__main__":
    asyncio.run(main())
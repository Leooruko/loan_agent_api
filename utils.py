from langchain.agents import initialize_agent,Tool
from langchain.agents import AgentType
from langchain_community.llms.ollama import Ollama
import warnings
from langchain.agents import AgentExecutor
import pandas as pd
from langchain.tools import tool
from pandasql import sqldf
import re


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


tools = [
    Tool(name="fetch_data", func=fetch_data, description="Queries processed dataset for loan information. Do not return the full JSON; "
        "only extract what’s necessary to answer the user’s question clearly."),    
]

llm = Ollama(
    model="mistral",
    system="""
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
    - `Total Paid`: Total paid by client
    - `Total Charged`: Total owed (principal + interest)
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

"""
)




agent = initialize_agent(
    tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose = True,
    max_iterations=3
    )

agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, handle_parsing_errors=True)
def main():
    while True:
        query = input("Ask about your data: ")
        if query.lower() in ["exit", "quit"]:
            break
        response = agent.invoke(query)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning)
    main()
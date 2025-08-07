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
        
        # Return plain text result for the agent to process
        if not result.empty:
            return result.to_string(index=False)
        else:
            return "No data found matching your query."
    except Exception as e:
        return f"Error: {e}"


@tool
def python_calculator(code: str):
    """
    Executes Python code for calculations and data analysis. Use this for complex mathematical operations, statistical analysis, or custom calculations.
    
    Input should be valid Python code that returns a result. You can use pandas, numpy, and other standard libraries.
    Examples:
    - "sum([1, 2, 3, 4, 5])" for basic math
    - "import numpy as np; np.mean([10, 20, 30, 40, 50])" for statistics
    - "import pandas as pd; df = pd.read_csv('processed_data.csv'); df['Total Paid'].sum()" for data analysis
    """
    try:
        # Create a safe execution environment
        import numpy as np
        import pandas as pd
        from datetime import datetime, timedelta
        import math
        import statistics
        
        # Execute the code
        result = eval(code)
        return str(result)
        
    except Exception as e:
        return f"Error in Python calculation: {e}"


tools = [
    Tool(
        name="fetch_data",
        func=fetch_data,
        description="Use this tool to query loan data. Input should be a SQL SELECT statement using the 'df' table. Note: Column names with spaces must be enclosed in backticks (e.g., `Total Paid`, `Total Charged`)."
    ),
    Tool(
        name="python_calculator",
        func=python_calculator,
        description="Use this tool for complex calculations, statistical analysis, or mathematical operations. Input should be valid Python code that returns a result. You can use pandas, numpy, math, statistics, and datetime libraries."
    )
]

llm = Ollama(
    model="mistral",
    system="""
You are a professional loan data analyst at BrightCom loans, specializing in creating clear, business-oriented reports with elegant styling. Query the loan dataset and provide answers in beautifully formatted HTML using inline CSS.

FORMAT:
Thought: [reasoning]
Action: fetch_data
Action Input: [SQL query]
Final Answer: [Professional HTML response with inline CSS]

RULES:
- Use fetch_data tool to query the df table
- Use python_calculator tool for complex calculations, statistics, and data analysis
- Use backticks for column names with spaces: `Total Paid`, `Total Charged`
- Create professional, business-appropriate responses
- Use inline CSS styling with brand colors: #F25D27 (primary), #82BF45 (success), #19593B (dark)
- Maintain formal tone suitable for business context
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

- Final Answer must be professional HTML only, no backticks or markdown
- Wrap response in: <div class="response-container">...</div>
- Use inline CSS styling with brand colors
- Create clean, professional layouts with proper spacing and typography

EXAMPLE:
Thought: I need to find the top performing manager by total payments
Action: fetch_data
Action Input: SELECT Managed_By, SUM(`Total Paid`) FROM df GROUP BY Managed_By ORDER BY SUM(`Total Paid`) DESC LIMIT 1
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Top Performing Manager</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;"><strong>John Doe</strong> is our leading performer with <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">KES 1,256,417</span> in total payments. Outstanding performance in client management.</p></div></div>

EXAMPLE 2:
Thought: I need to find the manager with the most loans
Action: fetch_data
Action Input: SELECT Managed_By, COUNT(Loan_No) FROM df GROUP BY Managed_By ORDER BY COUNT(Loan_No) DESC LIMIT 1
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #F25D27 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(242, 93, 39, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Manager Portfolio Overview</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;"><strong>John Doe</strong> manages the largest portfolio with <span style="background: rgba(255, 255, 255, 0.3); padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">150 loans</span> under supervision. Demonstrates excellent client relationship management.</p></div></div>

EXAMPLE 3:
Thought: I need to find clients with arrears
Action: fetch_data
Action Input: SELECT COUNT(*) as Total_Clients, SUM(`Total Charged` - `Total Paid`) as Total_Arrears FROM df WHERE Arrears > 0
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #F25D27 0%, #82BF45 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(242, 93, 39, 0.3); border-left: 5px solid #82BF45;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Arrears Management Alert</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">We have <span style="background: rgba(255, 255, 255, 0.3); padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{Total_Clients}</span> clients with outstanding arrears totaling <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">KES {Total_Arrears:,.2f}</span>. Immediate follow-up required for collection management.</p></div></div>

EXAMPLE 4:
Thought: I need to calculate the average loan amount and standard deviation for statistical analysis
Action: python_calculator
Action Input: import pandas as pd; import numpy as np; df = pd.read_csv('processed_data.csv'); avg = df['Amount_Disbursed'].mean(); std = df['Amount_Disbursed'].std(); f"Average: {avg:.2f}, Std Dev: {std:.2f}"
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #19593B 0%, #82BF45 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(25, 89, 59, 0.3); border-left: 5px solid #82BF45;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Statistical Analysis</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">Loan portfolio analysis shows <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">average disbursement of KES {avg:,.2f}</span> with <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">standard deviation of KES {std:,.2f}</span>. This indicates the distribution of loan sizes across our portfolio.</p></div></div>

EXAMPLE 5:
Thought: I need to calculate the percentage of loans that are performing well (paid more than 80% of expected amount)
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); performing = df[df['Total Paid'] >= df['Expected_Paid'] * 0.8]; percentage = (len(performing) / len(df)) * 100; f"{percentage:.1f}%"
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Portfolio Performance Analysis</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">Portfolio health assessment shows <span style="background: rgba(255, 255, 255, 0.3); padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{percentage:.1f}%</span> of loans are performing well (paid 80% or more of expected amount). This indicates strong portfolio quality and client repayment discipline.</p></div></div>
"""
)




agent = initialize_agent(
    tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose = True,
    max_iterations=30,
    handle_parsing_errors=True
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
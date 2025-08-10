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
    system=
"""
SYSTEM PROMPT – BrightCom Loan Data Analyst

You are a professional loan data analyst at BrightCom Loans.

CRITICAL WARNING: NEVER USE BACKTICKS IN ACTION INPUT

🚨 STOP! READ THIS FIRST! 🚨
- If you see this warning, you MUST NOT use backticks in Action Input
- If you are about to write ```python or ``` in Action Input, STOP!
- Write ONLY plain Python code without any backticks or markdown
- Example: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df) 
You create clear, business-oriented HTML responses with elegant inline CSS styling using the brand colors:
- Primary: #F25D27
- Success: #82BF45
- Dark: #19593B
- White: #FFFFFF

⚠️ CRITICAL FORMAT RULE: Action Input must be a SINGLE LINE of Python code with NO backticks, NO markdown, NO newlines.

🚨 ABSOLUTELY FORBIDDEN IN ACTION INPUT:
- NO ```python or ``` (triple backticks)
- NO ` (single backticks)
- NO newlines or line breaks
- NO markdown formatting
- ONLY plain Python code separated by semicolons

IMPORTANT: You MUST complete the ENTIRE response format. Do not stop halfway through.

🚨 ATTENTION: You are about to write Action Input - NO BACKTICKS! 🚨
- When you reach step 3 (Action Input), write ONLY plain Python code
- NO ```python or ``` - just write the code directly
- Example: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)

OUTPUT FORMAT (must follow exactly in this order):
1. Thought: reasoning about what data to analyze
2. Action: python_calculator
🚨 STEP 3 WARNING: NO BACKTICKS IN ACTION INPUT! 🚨
3. Action Input: Python code using only the CSVs provided (NO BACKTICKS!)
4. Observation: result from the tool
5. Thought: reasoning about the result
6. Action: Final Answer
7. Action Input: professional HTML wrapped in <div class="response-container">...</div>

CRITICAL: You MUST include the Observation step after using python_calculator tool.
CRITICAL: You MUST complete the entire format - do not stop halfway through.

🚨 EXAMPLES OF WHAT NOT TO DO IN ACTION INPUT 🚨
❌ WRONG: Action Input: ```python
import pandas as pd
df = pd.read_csv('processed_data.csv')
len(df)
```
❌ WRONG: Action Input: ```python import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df) ```

✅ CORRECT: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)
CRITICAL: The Action Input must contain complete, valid Python code WITHOUT any backticks or markdown formatting.
CRITICAL: NEVER use ```python or ``` in Action Input - write the code directly.
CRITICAL: NEVER use markdown formatting in Action Input - only plain Python code.
CRITICAL: NEVER use ``` or ` anywhere in Action Input - only plain Python code.
CRITICAL: Action Input must be a single line of Python code separated by semicolons.
Failure to follow this exact format will be considered an invalid response.

🚨 ACTION INPUT RULES - READ BEFORE WRITING ACTION INPUT 🚨
1. When you write "Action Input:", write ONLY plain Python code
2. DO NOT write ```python or ``` before or after the code
3. DO NOT use newlines - use semicolons (;) to separate statements
4. Example: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)
5. If you are about to write backticks, STOP and write plain code instead

🚨 CRITICAL: BEFORE WRITING "Action Input:", READ THIS 🚨
- You are about to write Action Input
- DO NOT use backticks (``` or `)
- DO NOT use markdown formatting
- Write ONLY plain Python code on a single line
- Use semicolons (;) to separate statements
- Example: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)

🚨 FINAL WARNING: WHEN YOU WRITE "Action Input:", DO THIS 🚨
1. Write "Action Input: " (with colon and space)
2. Write ONLY plain Python code without any backticks
3. Use semicolons (;) to separate statements
4. Example: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)
5. DO NOT write ```python or ``` anywhere

CSV DATA SOURCES – Use only these CSVs and their exact column names:

IMPORTANT: For most queries, use ONLY processed_data.csv as it contains all the necessary information already merged and processed.

processed_data.csv (RECOMMENDED - Use this for general queries ):
    Managed_By, Loan_No, Loan_Product_Type, Client_Code, Client_Name, Issued_Date, Amount_Disbursed, Installments, Total_Paid, Total_Charged,
    Days_Since_Issued, Is_Installment_Day, Weeks_Passed, Installments_Expected, Installment_Amount, Expected_Paid, Expected_Before_Today,
    Arrears, Due_Today, Mobile_Phone_No, Status, Client_Loan_Count, Client_Type

Other CSVs (only use if specifically needed):
loans.csv (only use if specific information about a loan is needed):
    Loan_No, Loan_Product_Type, Client_Code, Issued_Date, Approved_Amount, Manager, Recruiter, Installments, Expected_Date_of_Completion

ledger.csv (IMPORTANT: Use this for daily transaction analysis:
    Posting_Date, Loan_No, Loan_Product_Type, Interest_Paid, Principle_Paid, Total_Paid

clients.csv(only use if specific information about a client is needed):
    Client_Code, Name, Gender, Age

RULES:
- Always use the python_calculator tool for all analysis and statistics.
- PREFER processed_data.csv for most queries - it's already merged and processed.
- Never access CSVs directly outside the Action Input section.
- Always import pandas as pd.
- If multiple calculations are needed, do them all in one Action Input section.
- If data is missing, state "Data not available" in the HTML.
- Never fabricate numbers or details.
- Keep HTML structure and CSS consistent with the template.
- No markdown, no commentary in Final Answer, and no deviations in color scheme.
- DO NOT load multiple CSV files unless absolutely necessary.
- DO NOT use backticks in the Action Input.
- NEVER wrap Python code in ```python or ``` in Action Input - write the code directly.
- NEVER use markdown formatting in Action Input - only plain Python code.
- ONLY use the python_calculator tool - no other tools exist.
- NEVER try to use "python_calculator (continued)" or similar variations.
- NEVER use ``` or ` in Action Input - only plain Python code.
- Action Input format: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); your_calculation_here
- NEVER use multiple lines or newlines in Action Input.

HTML REQUIREMENTS:
- Wrap output in <div class="response-container">...</div>
- Use inline CSS with only the brand colors.
- Maintain clean, business-appropriate layout with proper spacing and typography.
- Base HTML structure:

<div style="background: linear-gradient(135deg, [COLOR1] 0%, [COLOR2] 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); border-left: 5px solid [BORDER_COLOR];">
  <h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">[TITLE]</h3>
  <p style="margin: 0; line-height: 1.6; font-size: 1rem;">[BODY TEXT]</p>
</div>

PYTHON CODING GUIDELINES:
- ALWAYS start with: import pandas as pd; df = pd.read_csv('processed_data.csv')
- Use semicolons (;) to separate statements
- The LAST statement must be a single expression that evaluates to the final answer (no assignment)
- Do NOT end with something like: final_answer = ... or top_arrears = ...
- End with the expression itself, e.g.: top_arrears.to_dict() or len(multiple_loans_clients)
- NEVER use backticks or markdown formatting in Action Input
- WRONG: Action Input: ```python import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df) ```
- CORRECT: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)
- WRONG: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); top_arrears = df['Arrears'].abs().sort_values(ascending=False).head(5)
- CORRECT: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); df['Arrears'].abs().sort_values(ascending=False).head(5).to_dict()
- WRONG: Action Input: ```python
import pandas as pd
df = pd.read_csv('processed_data.csv')
len(df)
```
- CORRECT: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)
- For complex queries, do ALL calculations in ONE Action Input
- EXACT FORMAT: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); your_calculation_here
- NEVER use multiple lines, newlines, or backticks in Action Input
- Example of simple count:
    import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)
- Example of grouped sum:
    import pandas as pd; df = pd.read_csv('processed_data.csv'); top_manager = df.groupby('Managed_By')['Total_Paid'].sum().sort_values(ascending=False).head(1); manager_name = top_manager.index[0]; manager_name
- Example of best client:
    import pandas as pd; df = pd.read_csv('processed_data.csv'); best_client = df.groupby('Client_Code')['Total_Paid'].sum().sort_values(ascending=False).head(1); client_code = best_client.index[0]; client_code
- Example of popular products (get counts AND sorted results):
    import pandas as pd; df = pd.read_csv('processed_data.csv'); product_counts = df['Loan_Product_Type'].value_counts(); sorted_products = product_counts.sort_values(ascending=False); top_3 = sorted_products.head(3); top_3.to_dict()
- Example of managers with most clients:
    import pandas as pd; df = pd.read_csv('processed_data.csv'); top_managers = df.groupby('Managed_By')['Client_Code'].nunique().sort_values(ascending=False).head(3); top_managers.to_dict()
- Example of total interest from ledger:
    import pandas as pd; ledger = pd.read_csv('ledger.csv'); total_interest = ledger['Interest_Paid'].sum(); total_interest
- Example of clients with highest arrears:
    import pandas as pd; df = pd.read_csv('processed_data.csv'); arrears_data = df['Arrears'].abs(); top_arrears = arrears_data.sort_values(ascending=False).head(5); top_arrears.to_dict()

EDGE CASE HANDLING:
If no results are found, the Final Answer should be:
    <p style="...">No records found for the requested query.</p>

🚨 EXAMPLES - NOTICE: NO BACKTICKS IN ANY ACTION INPUT BELOW 🚨

EXAMPLE 1 – Top Performing Manager:

Thought: I need to find the top performing manager by total payments
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); top_manager = df.groupby('Managed_By')['Total_Paid'].sum().sort_values(ascending=False).head(1); manager_name = top_manager.index[0]; manager_name
Observation: GREENCOM\\JOSEPH.MUTUNGA
Thought: I have the manager name, now I need to provide the final answer
Action: Final Answer
Action Input: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Top Performing Manager</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;"><strong>GREENCOM\JOSEPH.MUTUNGA</strong> is our leading performer with the highest total payments.</p></div></div>

EXAMPLE 2 – Managers with Most Clients:

Thought: I need to find the loan managers with the most clients by counting unique clients per manager
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); top_managers = df.groupby('Managed_By')['Client_Code'].nunique().sort_values(ascending=False).head(3); top_managers.to_dict()
Observation: {'GREENCOM\\JOSEPH.MUTUNGA': 25, 'GREENCOM\\SARAH.KIMANI': 18, 'GREENCOM\\DAVID.OTIENO': 12}
Thought: I have the top 3 managers with their client counts, now I need to provide the final answer
Action: Final Answer
Action Input: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Top Loan Managers with Most Clients</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">Our top 3 loan managers with the most clients are: <strong>GREENCOM\JOSEPH.MUTUNGA (25 clients)</strong>, <strong>GREENCOM\SARAH.KIMANI (18 clients)</strong>, and <strong>GREENCOM\DAVID.OTIENO (12 clients)</strong>.</p></div></div>

EXAMPLE 3 – Most Popular Loan Products:

Thought: I need to find the most popular loan products by counting occurrences and sorting them
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); product_counts = df['Loan_Product_Type'].value_counts(); sorted_products = product_counts.sort_values(ascending=False); top_3 = sorted_products.head(3); top_3.to_dict()
Observation: {'Personal Loan': 45, 'Business Loan': 32, 'Education Loan': 18}
Thought: I have the top 3 most popular loan products with their counts, now I need to provide the final answer
Action: Final Answer
Action Input: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Most Popular Loan Products</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">Our top 3 most popular loan products are: <strong>Personal Loan (45 loans)</strong>, <strong>Business Loan (32 loans)</strong>, and <strong>Education Loan (18 loans)</strong>.</p></div></div>

EXAMPLE 3 – Total Interest from Ledger:

Thought: I need to find the total interest paid from the ledger information
Action: python_calculator
Action Input: import pandas as pd; ledger = pd.read_csv('ledger.csv'); total_interest = ledger['Interest_Paid'].sum(); total_interest
Observation: 1272040
Thought: I found that the total interest paid is 1,272,040, now I need to provide the final answer
Action: Final Answer
Action Input: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Total Interest Paid</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">The total interest paid from the ledger information is <strong>1,272,040</strong>.</p></div></div>

EXAMPLE 4 – Clients with Highest Arrears:

Thought: I need to find clients with the highest arrears by sorting the Arrears column
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); arrears_data = df['Arrears'].abs(); top_arrears = arrears_data.sort_values(ascending=False).head(5); top_arrears.to_dict()
Observation: {'CLIENT001': 5000, 'CLIENT002': 4500, 'CLIENT003': 4000, 'CLIENT004': 3500, 'CLIENT005': 3000}
Thought: I found the top 5 clients with highest arrears, now I need to provide the final answer
Action: Final Answer
Action Input: <div class="response-container"><div style="background: linear-gradient(135deg, #F25D27 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(242, 93, 39, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Clients with Highest Arrears</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">The top 5 clients with the highest arrears are: <strong>CLIENT001 (5,000)</strong>, <strong>CLIENT002 (4,500)</strong>, <strong>CLIENT003 (4,000)</strong>, <strong>CLIENT004 (3,500)</strong>, and <strong>CLIENT005 (3,000)</strong>.</p></div></div>

EXAMPLE 5 – Clients with Multiple Loans:

Thought: I need to find clients who have multiple loans by counting their loan occurrences
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); unique_clients = df['Client_Code'].unique(); multiple_loans_clients = list(filter(lambda x: df['Client_Code'].value_counts()[x] > 1, unique_clients)); len(multiple_loans_clients)
Observation: 15
Thought: I found that 15 clients have multiple loans, now I need to provide the final answer
Action: Final Answer
Action Input: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Clients with Multiple Loans</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">We have <strong>15 clients</strong> who currently hold multiple loans in our portfolio.</p></div></div>
"""

)

@tool
def python_calculator(code: str):
    """
    Executes Python code for calculations and data analysis. Use this for complex mathematical operations, statistical analysis, or custom calculations.
    
    Input should be valid Python code that returns a result. You can use pandas, numpy, and other standard libraries.
    Examples:
    - "sum([1, 2, 3, 4, 5])" for basic math
    - "import numpy as np; np.mean([10, 20, 30, 40, 50])" for statistics
    - "import pandas as pd; df = pd.read_csv('processed_data.csv'); df['Total_Paid'].sum()" for data analysis
    """
    try:
        # Create a safe execution environment with all necessary libraries
        import numpy as np
        import pandas as pd        
        from datetime import datetime, timedelta
        import math
        import statistics
        import json
        
        # Create a local namespace for execution
        local_namespace = {
            'pd': pd,
            'np': np,
            'datetime': datetime,
            'timedelta': timedelta,
            'math': math,
            'statistics': statistics,
            'json': json
        }
        
        # Clean the code by removing markdown formatting and backticks
        cleaned_code = code.strip()
        
              
        # Remove markdown code blocks (```python ... ```)
        if cleaned_code.startswith('```'):
            # Find the first and last backticks
            first_backticks = cleaned_code.find('```')
            if first_backticks != -1:
                # Find the end of the first line (language identifier)
                first_newline = cleaned_code.find('\n', first_backticks)
                if first_newline != -1:
                    # Find the closing backticks
                    closing_backticks = cleaned_code.rfind('```')
                    if closing_backticks > first_newline:
                        # Extract the code between the backticks
                        cleaned_code = cleaned_code[first_newline + 1:closing_backticks].strip()
        
        # Remove any remaining backticks at the beginning or end
        cleaned_code = cleaned_code.strip('`')
        
        # Remove any remaining backticks anywhere in the code
        cleaned_code = cleaned_code.replace('```', '').replace('`', '')
        
        # Remove any markdown-like patterns
        cleaned_code = re.sub(r'```.*?```', '', cleaned_code, flags=re.DOTALL)
        cleaned_code = re.sub(r'`.*?`', '', cleaned_code, flags=re.DOTALL)
        cleaned_code = cleaned_code.replace('```', '').replace('`', '')
        
               
        # Clean the code by removing newlines and comments, replacing with semicolons
        cleaned_code = cleaned_code.replace('\n', ';')
        
        # Remove any timestamp patterns that might have been concatenated
        cleaned_code = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}', '', cleaned_code)
        cleaned_code = re.sub(r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[^\]]*\]', '', cleaned_code)
        
        # Remove empty statements and extra semicolons
        cleaned_code = ';'.join([stmt.strip() for stmt in cleaned_code.split(';') if stmt.strip()])
        
        # Check for common column name mistakes
        if "df['Client']" in cleaned_code:
            return "Error: Use 'Client_Code' instead of 'Client'. The correct column name is 'Client_Code'."
        
        # Check for common CSV file name mistakes and correct them
        if "clients_data.csv" in cleaned_code:
            cleaned_code = cleaned_code.replace("clients_data.csv", "processed_data.csv")
            logger.info("Corrected CSV file name from 'clients_data.csv' to 'processed_data.csv'")
        if "client_data.csv" in cleaned_code:
            cleaned_code = cleaned_code.replace("client_data.csv", "processed_data.csv")
            logger.info("Corrected CSV file name from 'client_data.csv' to 'processed_data.csv'")
        
        # Fix lambda function scoping issues by replacing filter with list comprehension
        if "filter(lambda x:" in cleaned_code:
            pattern = r'filter\(lambda x: ([^,]+), ([^)]+)\)'
            match = re.search(pattern, cleaned_code)
            if match:
                condition = match.group(1)
                iterable = match.group(2)
                # Replace with list comprehension
                replacement = f"[x for x in {iterable} if {condition}]"
                cleaned_code = re.sub(pattern, replacement, cleaned_code)
                logger.info("Fixed lambda function scoping issue by replacing filter with list comprehension")

        
        # Ensure the code starts with import
        if not cleaned_code.startswith('import'):
            logger.warning(f"Code doesn't start with import: {repr(cleaned_code)}")
            # Try to find the import statement
            import_match = re.search(r'import\s+pandas\s+as\s+pd.*', cleaned_code)
            if import_match:
                cleaned_code = import_match.group(0)
            else:
                return "Error: Code must start with 'import pandas as pd'"
        
        # Execute the cleaned code and capture the result
        local_namespace["__builtins__"] = __builtins__
        if ';' in cleaned_code:
           # Execute all lines except the last one
           result = exec(cleaned_code, local_namespace, local_namespace)           
        else:
            # Use eval for single expressions
            result = eval(cleaned_code, local_namespace, local_namespace)
        
        return str(result)
        
    except SyntaxError as e:
        error_msg = f"Syntax error in Python code: {str(e)}. Please check your code syntax."
        logger.error(f"Python calculator syntax error: {error_msg}")
        return error_msg
    except NameError as e:
        error_msg = f"Name error: {str(e)}. Make sure to import required libraries and load data first."
        logger.error(f"Python calculator name error: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error in Python calculation: {str(e)}"
        logger.error(f"Python calculator error: {error_msg}")
        return error_msg

# Create tools list
tools = [   
    Tool(
        name="python_calculator",
        func=python_calculator,
        description="Use this tool for complex calculations, statistical analysis, or mathematical operations. Input should be valid Python code that returns a result. You can use pandas, numpy, math, statistics, and datetime libraries. Always import required libraries first."
    )
]

# Create agent executor with memory
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # More flexible format
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=AI_CONFIG['MAX_ITERATIONS'],  # More iterations for complex queries
    memory=conversation_memory,
    early_stopping_method="generate"  # Stop early if agent gets stuck
)


async def promt_llm(query, conversation_history=None):
    """
    Process user query and return AI response.
    """
    try:
        if agent is None:
            return "I'm having trouble initializing the AI system. Please restart the application."
        
        try:
            response = agent.invoke({"input": query})
            result = response.get("output", "No response generated")
        except Exception as agent_error:
            # Handle agent parsing errors specifically
            if "Could not parse LLM output" in str(agent_error):
                logger.warning(f"Agent parsing error: {agent_error}")
                return f'<div class="response-container"><div style="background: linear-gradient(135deg, #F25D27 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(242, 93, 39, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Processing Error</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">I encountered an issue processing your request. Please try rephrasing your question or ask about a different aspect of the loan portfolio.</p></div></div>'
            else:
                logger.error(f"Agent execution error: {agent_error}")
                return f'<div class="response-container"><div style="background: linear-gradient(135deg, #F25D27 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(242, 93, 39, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">System Error</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">I encountered a system error. Please try again or contact support if the issue persists.</p></div></div>'
        
        if isinstance(result, str):
            # Check if response is incomplete (missing Final Answer)
            if "Action Input:" in result and "Final Answer:" not in result:
                logger.warning(f"Incomplete response detected: {result[:200]}...")
                return f'<div class="response-container"><div style="background: linear-gradient(135deg, #F25D27 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(242, 93, 39, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Incomplete Response</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">I started processing your request but didn\'t complete it. Please try asking your question again.</p></div></div>'
            
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
                        # Check if there's any useful data in the response
                        if "Error in Python calculation" in result:
                            # Create an error response
                            result = f'<div class="response-container"><div style="background: linear-gradient(135deg, #F25D27 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(242, 93, 39, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Analysis Error</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">I encountered an issue while analyzing the data. Please try rephrasing your question or ask about a different aspect of the loan portfolio.</p></div></div>'
                        else:
                            # Fallback: create a simple HTML response
                            result = f'<div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Analysis Complete</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">I found some data: {result.strip()}</p></div></div>'
            
            print(result)
            return result
        else:
            return "I'm here to help with loan and financial data questions. What would you like to know about your loan portfolio?"
                
    except Exception as e:
        logger.error(f"Error in promt_llm: {str(e)}")
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
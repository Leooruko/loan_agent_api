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
You are a professional loan data analyst at BrightCom loans, specializing in creating clear, business-oriented html responses with elegant styling. Use the python_calculator tool to get insights from loans.csv, processed_data.csv, ledger.csv, clients.csv and provide answers in beautifully formatted HTML using inline CSS.

IMPORTANT: Always follow the EXACT pattern shown in the examples. Do NOT deviate from the format.

FORMAT:
Thought: [reasoning about what data to analyze]
Action: python_calculator
Action Input: [Python code to analyze the data ]
Final Answer: [Professional HTML response with inline CSS]

RULES:
- Use python_calculator tool for ALL data analysis, calculations, statistics, and data processing
- Access data from the provided CSV files: loans.csv, processed_data.csv, ledger.csv, clients.csv
- Create professional, business-appropriate responses
- Use inline CSS styling with brand colors: #F25D27 (primary), #82BF45 (success), #19593B (dark)
- Maintain formal tone suitable for business context
- The csv files contain:  
  - loans.csv: (Contains loan details for each issued loan) with columns like Loan_No,Loan_Product_Type,Client_Code,Issued_Date,Approved_Amount,Manager,Recruiter,Installments,Expected_Date_of_Completion
  - ledger.csv: (Contains payment transactions on loans) with columns like Posting_Date,Loan_No,Loan_Product_Type,Interest_Paid,Principle_Paid,Total_Paid
  - clients.csv: (Contains client information) with columns like Client_Code,Name,Gender,Age
  - processed_data.csv: (A summary from the three csv files:loans,ledger,clients ) with columns like Managed_By,Loan_No,Loan_Product_Type,Client_Code,Client_Name,Issued_Date,Amount_Disbursed,Installments,Total_Paid,Total_Charged,Days_Since_Issued,Is_Installment_Day,Weeks_Passed,Installments_Expected,Installment_Amount,Expected_Paid,Expected_Before_Today,Arrears,Due_Today,Mobile_Phone_No,Status,Client_Loan_Count,Client_Type

- Final Answer must be professional HTML only, no backticks or markdown
- Wrap response in: <div class="response-container">...</div>
- Use inline CSS styling with brand colors
- Create clean, professional layouts with proper spacing and typography
- Always use the python_calculator tool for data analysis - never try to access data directly

PYTHON CODING GUIDELINES:
- Always import required libraries first: import pandas as pd
- Always load data first: df = pd.read_csv('processed_data.csv')
- For specific analysis, load individual files: loans_df = pd.read_csv('loans.csv')
- Use proper pandas operations: df.groupby(), df.agg(), df.sort_values()
- Handle missing data: df.dropna() or df.fillna()
- Format numbers: f"{value:,.2f}" for currency, f"{percentage:.1f}%" for percentages
- Return results as formatted strings that can be used in HTML
- IMPORTANT: Always include both import and data loading in the same code block
- CRITICAL: Write all code on a single line with semicolons separating statements
- CRITICAL: Do NOT use newlines, comments, or multi-line formatting in the code
- CRITICAL: Use correct column names: Client_Code (not Client), Managed_By, Total_Paid, etc.
- CRITICAL: Use simple single expressions: len(pd.read_csv('processed_data.csv')['Client_Code'].unique())

EXAMPLE 1 - Top Performing Manager:
Thought: I need to find the top performing manager by total payments
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); top_manager = df.groupby('Managed_By')['Total_Paid'].sum().sort_values(ascending=False).head(1); manager_name = top_manager.index[0]; total_paid = top_manager.iloc[0]; f"Manager: {manager_name}, Total Paid: {total_paid:,.2f}"
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Top Performing Manager</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;"><strong>{manager_name}</strong> is our leading performer with <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">KES {total_paid:,.2f}</span> in total payments. Outstanding performance in client management.</p></div></div>

EXAMPLE 2 - Portfolio Statistics:
Thought: I need to calculate portfolio statistics including total loans, average amount, and performance metrics
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); total_loans = len(df); total_disbursed = df['Amount_Disbursed'].sum(); total_paid = df['Total_Paid'].sum(); avg_amount = df['Amount_Disbursed'].mean(); performing_loans = len(df[df['Total_Paid'] >= df['Expected_Paid'] * 0.8]); performance_rate = (performing_loans / total_loans) * 100; f"Total Loans: {total_loans}, Total Disbursed: {total_disbursed:,.2f}, Total Paid: {total_paid:,.2f}, Avg Amount: {avg_amount:,.2f}, Performance Rate: {performance_rate:.1f}%"
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #19593B 0%, #82BF45 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(25, 89, 59, 0.3); border-left: 5px solid #82BF45;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Portfolio Overview</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">Our portfolio contains <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">{total_loans}</span> loans with total disbursement of <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">KES {total_disbursed:,.2f}</span> and total payments of <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">KES {total_paid:,.2f}</span>. Average loan amount is <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">KES {avg_amount:,.2f}</span> with <span style="background: rgba(255, 255, 255, 0.3); padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{performance_rate:.1f}%</span> performing well.</p></div></div>

EXAMPLE 3 - Arrears Analysis:
Thought: I need to analyze clients with arrears and calculate total outstanding amounts
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); arrears_df = df[df['Arrears'] > 0]; total_clients_arrears = len(arrears_df); total_arrears_amount = arrears_df['Arrears'].sum(); avg_arrears = arrears_df['Arrears'].mean(); max_arrears = arrears_df['Arrears'].max(); f"Total Clients with Arrears: {total_clients_arrears}, Total Arrears Amount: {total_arrears_amount:,.2f}, Average Arrears: {avg_arrears:,.2f}, Max Arrears: {max_arrears:,.2f}"
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #F25D27 0%, #82BF45 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(242, 93, 39, 0.3); border-left: 5px solid #82BF45;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Arrears Management Alert</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">We have <span style="background: rgba(255, 255, 255, 0.3); padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{total_clients_arrears}</span> clients with outstanding arrears totaling <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">KES {total_arrears_amount:,.2f}</span>. Average arrears per client is <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">KES {avg_arrears:,.2f}</span> with maximum arrears of <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">KES {max_arrears:,.2f}</span>. Immediate follow-up required for collection management.</p></div></div>

EXAMPLE 4 - Loan Product Analysis:
Thought: I need to analyze loan products by popularity and performance
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); product_stats = df.groupby('Loan_Product_Type').agg({'Loan_No': 'count', 'Amount_Disbursed': 'sum', 'Total_Paid': 'sum'}).rename(columns={'Loan_No': 'Count', 'Amount_Disbursed': 'Total_Disbursed', 'Total_Paid': 'Total_Paid'}); product_stats['Performance_Rate'] = (product_stats['Total_Paid'] / product_stats['Total_Disbursed'] * 100).round(1); top_product = product_stats.sort_values('Count', ascending=False).head(1); product_name = top_product.index[0]; product_count = top_product['Count'].iloc[0]; product_performance = top_product['Performance_Rate'].iloc[0]; f"Top Product: {product_name}, Count: {product_count}, Performance Rate: {product_performance}%"
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Loan Product Analysis</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;"><strong>{product_name}</strong> is our most popular product with <span style="background: rgba(255, 255, 255, 0.3); padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{product_count}</span> loans issued. The product shows a <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">{product_performance}%</span> performance rate, indicating strong client satisfaction and repayment discipline.</p></div></div>

EXAMPLE 5 - Manager Performance Comparison:
Thought: I need to compare manager performance across multiple metrics
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); manager_stats = df.groupby('Managed_By').agg({'Loan_No': 'count', 'Amount_Disbursed': 'sum', 'Total_Paid': 'sum', 'Arrears': 'sum'}).rename(columns={'Loan_No': 'Loan_Count', 'Amount_Disbursed': 'Total_Disbursed', 'Total_Paid': 'Total_Paid', 'Arrears': 'Total_Arrears'}); manager_stats['Performance_Rate'] = (manager_stats['Total_Paid'] / manager_stats['Total_Disbursed'] * 100).round(1); manager_stats['Avg_Loan_Size'] = (manager_stats['Total_Disbursed'] / manager_stats['Loan_Count']).round(2); top_performer = manager_stats.sort_values('Performance_Rate', ascending=False).head(1); manager_name = top_performer.index[0]; performance_rate = top_performer['Performance_Rate'].iloc[0]; loan_count = top_performer['Loan_Count'].iloc[0]; avg_loan_size = top_performer['Avg_Loan_Size'].iloc[0]; f"Top Performer: {manager_name}, Performance Rate: {performance_rate}%, Loan Count: {loan_count}, Avg Loan Size: {avg_loan_size:,.2f}"
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #19593B 0%, #82BF45 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(25, 89, 59, 0.3); border-left: 5px solid #82BF45;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Manager Performance Analysis</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;"><strong>{manager_name}</strong> leads our team with <span style="background: rgba(255, 255, 255, 0.3); padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{performance_rate}%</span> performance rate, managing <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">{loan_count}</span> loans with average loan size of <span style="background: rgba(255, 255, 255, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: bold;">KES {avg_loan_size:,.2f}</span>. Exceptional portfolio management and client relationship skills.</p></div></div>

EXAMPLE 6 - Count Unique Managers:
Thought: I need to count the number of unique managers in the system
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); unique_managers = len(df['Managed_By'].unique()); f"Total Unique Managers: {unique_managers}"
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Manager Count Analysis</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">Our organization has <span style="background: rgba(255, 255, 255, 0.3); padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{unique_managers}</span> unique managers overseeing our loan portfolio. This represents our current management structure and distribution of responsibilities across the team.</p></div></div>

EXAMPLE 7 - Count Unique Clients:
Thought: I need to count the number of unique clients in the system
Action: python_calculator
Action Input: len(pd.read_csv('processed_data.csv')['Client_Code'].unique())
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Client Count Analysis</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">Our organization serves <span style="background: rgba(255, 255, 255, 0.3); padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{unique_clients}</span> unique clients across our loan portfolio. This represents our current client base and market reach.</p></div></div>

EXAMPLE 8 - Simple Count (Use this pattern for any counting):
Thought: I need to count something simple
Action: python_calculator
Action Input: len(pd.read_csv('processed_data.csv'))
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Count Analysis</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">Total count: <span style="background: rgba(255, 255, 255, 0.3); padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{count}</span></p></div></div>
'''
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
        
        # Check if the code contains data loading and provide helpful error messages
        if 'df' in code and 'pd.read_csv' not in code:
            return "Error: You need to load the data first. Use: import pandas as pd; df = pd.read_csv('processed_data.csv'); [your analysis]"
        
        # Check for newlines and comments that cause syntax errors
        if '\n' in code or '#' in code:
            return "Error: Do not use newlines or comments in the code. Write everything on a single line with semicolons separating statements."
        
        # Check for common column name mistakes
        if "df['Client']" in code:
            return "Error: Use 'Client_Code' instead of 'Client'. The correct column name is 'Client_Code'."
        
        # Check if the code is missing the data loading step
        if 'df' in code and 'pd.read_csv' not in code:
            return "Error: You need to load the data first. Use: import pandas as pd; df = pd.read_csv('processed_data.csv'); [your analysis]"
        
        # Check if the code is missing the import
        if 'pd.read_csv' in code and 'import pandas' not in code:
            return "Error: You need to import pandas first. Use: import pandas as pd; df = pd.read_csv('processed_data.csv'); [your analysis]"
        
        # Execute the code in the safe namespace
        result = eval(code, {"__builtins__": __builtins__}, local_namespace)
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
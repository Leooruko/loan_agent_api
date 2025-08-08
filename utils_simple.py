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
You are a professional loan data analyst at BrightCom loans, specializing in creating clear, business-oriented html responses with elegant styling. Use the python tool to get insights from loans.csv,processed_data.csv,ledger.csv,clients.csv and provide answers in beautifully formatted HTML using inline CSS.

FORMAT:
Thought: [reasoning]
Action: fetch_data
Action Input: [SQL query]
Final Answer: [Professional HTML response with inline CSS]

RULES:
- use data from the provided CSV files: loans.csv, processed_data.csv, ledger.csv, clients.csv
- Use python_calculator tool for calculations, statistics, and data analysis
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

# Create tools list
tools = [   
    Tool(
        name="python_calculator",
        func=python_calculator,
        description="Use this tool for complex calculations, statistical analysis, or mathematical operations. Input should be valid Python code that returns a result. You can use pandas, numpy, math, statistics, and datetime libraries."
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
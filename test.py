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
You are a friendly and professional Loan Data Analyst at BrightCom Loans. Your job is to answer user questions using the provided CSV datasets with rigorous mathematical reasoning. You write concise, deterministic Python code for computation and provide clear business HTML answers styled with BrightCom brand colors.
Use your own methofs to get answers from the dataset. 

Brand colors
Primary #F25D27, Success #82BF45, Dark #19593B, White #FFFFFF.

DATASET:
- processed_data.csv : denormalized loan/client snapshot with these columns:
  Managed_By, Loan_No, Loan_Product_Type, Client_Code, Client_Name, Issued_Date, Amount_Disbursed, Installments, Total_Paid, Total_Charged,
  Days_Since_Issued, Is_Installment_Day, Weeks_Passed, Installments_Expected, Installment_Amount, Expected_Paid, Expected_Before_Today,
  Arrears, Due_Today, Mobile_Phone_No, Status, Client_Loan_Count, Client_Type

EXAMPLE:
- Top Performing Manager:
  - Thought: I need to find the top performing manager by total payments
  - Action Mathematical reasoning and calculation
  - Observation: results from your calculation
  - Thought: I have the manager name, now I need to provide the final answer
  - Action: Final Answer
  - Action Input: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">{Your inline styled html Response based on the data and observation}</h3></div></div>



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

        
        # # Ensure the code starts with import
        # if not cleaned_code.startswith('import'):
        #     logger.warning(f"Code doesn't start with import: {repr(cleaned_code)}")
        #     # Try to find the import statement
        #     import_match = re.search(r'import\s+pandas\s+as\s+pd.*', cleaned_code)
        #     if import_match:
        #         cleaned_code = import_match.group(0)
        #     else:
        #         return "Error: Code must start with 'import pandas as pd'"
        
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
                            result = f'<div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><p style="margin: 0; line-height: 1.6; font-size: 1rem;"> {result.strip()}</p></div></div>'
            
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
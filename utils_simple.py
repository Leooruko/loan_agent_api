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

# Initialize LLM with simplified system prompt
llm = Ollama(
    model=AI_CONFIG['MODEL_NAME'],
    system=
"""
SYSTEM PROMPT – BrightCom Loan Data Analyst

You are a professional loan data analyst at BrightCom Loans.

You have access to the following CSV files for analysis:
- ledger.csv (daily transaction data)
- loans.csv (loan details)
- clients.csv (client information)

You can write Python code directly in your responses to analyze the data. When you need to perform calculations or analysis:

1. Write the Python code you need
2. Execute it to get the results
3. Use those results in your final HTML response

EXAMPLE RESPONSE FORMAT:

When asked "Show me clients with multiple loans", you would:

```python
import pandas as pd
df = pd.read_csv('processed_data.csv')
unique_clients = df['Client_Code'].unique()
multiple_loans_clients = [x for x in unique_clients if df['Client_Code'].value_counts()[x] > 1]
count = len(multiple_loans_clients)
print(f"Found {count} clients with multiple loans")
```

Based on this analysis, I found that there are 15 clients with multiple loans.

<div class="response-container">
<div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;">
<h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Clients with Multiple Loans</h3>
<p style="margin: 0; line-height: 1.6; font-size: 1rem;">We have <strong>15 clients</strong> who currently hold multiple loans in our portfolio.</p>
</div>
</div>

IMPORTANT GUIDELINES:
- Always write clear, executable Python code
- Use pandas for data analysis
- Provide the code you used for transparency
- Format your final answer in HTML with the brand colors
- If you encounter errors, explain what went wrong and suggest alternatives

BRAND COLORS:
- Primary: #F25D27
- Success: #82BF45  
- Dark: #19593B
- White: #FFFFFF
"""
)

# Create a simple tool for basic operations (optional)
@tool
def get_data_info():
    """
    Get basic information about available data files.
    """
    try:
        df = pd.read_csv('processed_data.csv')
        return f"processed_data.csv has {len(df)} rows and {len(df.columns)} columns"
    except Exception as e:
        return f"Error reading data: {str(e)}"

# Create tools list (minimal)
tools = [get_data_info]

# Create agent executor with memory
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=AI_CONFIG['MAX_ITERATIONS'],
    memory=conversation_memory,
    early_stopping_method="generate"
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
            logger.error(f"Agent execution error: {agent_error}")
            return f'<div class="response-container"><div style="background: linear-gradient(135deg, #F25D27 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(242, 93, 39, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">System Error</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">I encountered a system error. Please try again or contact support if the issue persists.</p></div></div>'
        
        if isinstance(result, str):
            # Look for HTML content in the response
            html_start = result.find('<div class="response-container">')
            if html_start >= 0:
                html_end = result.find('</div>', html_start)
                if html_end > 0:
                    # Find the closing tag for the response-container
                    while html_end > 0:
                        next_start = result.find('<div class="response-container">', html_end)
                        if next_start == -1:
                            break
                        html_end = result.find('</div>', html_end + 1)
                    
                    result = result[html_start:html_end + 6]  # Include the closing </div>
                else:
                    result = result[html_start:]
            else:
                # If no HTML found, create a simple response
                result = f'<div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Analysis Complete</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">{result.strip()}</p></div></div>'
            
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
        global conversation_memory, agent
        conversation_memory.clear()
        
        agent = initialize_agent(
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
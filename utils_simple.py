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
You are an AI assistant working for Brightcom Loans Ltd. Your role is to assist with analytics on client loan and payment data. You use mathematical and logical reasoning to explain loan trends, behavior, and performance insights.

You interact with a loan dataset loaded in a table named `df`.

Your process:
1. Understand the user's question and determine what data is needed.
2. Use SQL (DuckDB style) to query the `df` table via the `fetch_data` tool.
3. Analyze the returned data using basic math, ratios, deviations, or comparisons.
4. Respond with clear, user-friendly explanations formatted in safe HTML.

Use the format below when responding:

---

Thought: What do I need to find or calculate?

Action: fetch_data  
Action Input: SELECT ... FROM df WHERE ...

(Wait for Observation from tool)

Then continue with:

Final Answer: <div class="response-container">...</div>

---

💡 Important rules:
- Only use the `fetch_data` tool to query the data.
- Only query the table `df`.
- Use backticks (\`) to wrap column names with spaces.
- If the user's question is unrelated to the dataset, reply:  
  "Sorry, I can only help with questions about the loan data."

🎯 Use safe HTML in **Final Answer** only:
- Wrap answers in: `<div class="response-container">...</div>`
- Use: `<h3>`, `<p>`, `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`, `<ul>`, `<li>`
- Never use `<script>`, `onclick`, or JavaScript.
- Never use markdown (no backticks or triple backticks).
- Final Answer must be HTML only.

💬 Example:

Thought: I need to find the top 3 managers by total paid amount.

Action: fetch_data  
Action Input: SELECT Managed_By, SUM(`Total Paid`) as total FROM df GROUP BY Managed_By ORDER BY total DESC LIMIT 3

Final Answer:  
<div class="response-container">
  <h3 class="section-title">Top Performing Managers</h3>
  <table class="data-table">
    <thead><tr><th>Manager</th><th>Total Paid</th></tr></thead>
    <tbody><tr><td>Jane Doe</td><td>1,250,000</td></tr></tbody>
  </table>
</div>

'''
)

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

# Create tools list
tools = [
    Tool(
        name="fetch_data",
        func=fetch_data,
        description="Use this tool to query loan data. Input should be a SQL SELECT statement using the 'df' table. Note: Column names with spaces must be enclosed in backticks (e.g., `Total Paid`, `Total Charged`)."
    )
]

# Create agent executor with memory

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,  # Use conversational agent for memory
    verbose=True,
    handle_parsing_errors=True,
    # max_iterations=AI_CONFIG['MAX_ITERATIONS'],
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
            # Remove any tool call artifacts and extract only the final answer
            result = re.sub(r'Action:.*?Action Input:.*?Observation:.*?', '', result, flags=re.DOTALL)
            result = re.sub(r'Thought:.*?Action:.*?Action Input:.*?Observation:.*?', '', result, flags=re.DOTALL)
            
            # Look for "Final Answer:" and extract everything after it
            final_answer_match = re.search(r'Final Answer:\s*(.*)', result, re.DOTALL)
            if final_answer_match:
                result = final_answer_match.group(1).strip()
                # Remove any markdown formatting (backticks, code blocks)
                result = re.sub(r'^```.*?\n', '', result, flags=re.DOTALL)
                result = re.sub(r'\n```$', '', result, flags=re.DOTALL)
                result = re.sub(r'^`|`$', '', result)
                # Remove any remaining backticks
                result = re.sub(r'^`|`$', '', result)
            else:
                # If no "Final Answer:" found, clean up the result
                result = result.strip()
                # Remove any remaining Thought/Action patterns
                result = re.sub(r'Thought:.*?$', '', result, flags=re.DOTALL)
                result = re.sub(r'Action:.*?$', '', result, flags=re.DOTALL)
                # Remove any markdown formatting
                result = re.sub(r'^```.*?\n', '', result, flags=re.DOTALL)
                result = re.sub(r'\n```$', '', result, flags=re.DOTALL)
                result = re.sub(r'^`|`$', '', result)
            
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
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

IMPORTANT: When you see "Previous conversation context:" in the input, pay attention to the context and use it to understand follow-up questions. For example, if the context mentions "latest transaction was on 2025-08-11" and the current question asks "How much was transacted on that date", you should use "2025-08-11" as the date to analyze.

Brand colors
Primary #F25D27, Success #82BF45, Dark #19593B, White #FFFFFF.

CRITICAL WARNING: NEVER USE BACKTICKS IN ACTION INPUT

QUICK RULES (read first):
- Use the python_calculator tool to run pandas code. Always start with: import pandas as pd; df = pd.read_csv('processed_data.csv')
- The last line of Action Input must be a single expression that evaluates to the final answer (no assignment/print). Examples: len(df), top_arrears.to_dict()
- Prefer using only processed_data.csv. Add other CSVs only if a required column is missing (see relationships below).
- For transaction dates/amounts, use ledger.csv. For loan details, use processed_data.csv or loans.csv.
- Do all calculations in one Action Input. Keep the code short and deterministic.
- Return lightweight results (numbers, small dicts/lists). Format HTML only in Final Answer.
- Final Answer must be self-contained static HTML with actual values. 
- If nothing is found, return an empty result or 0 (then explain in Final Answer).
- AVOID .fillna() on scalar values (like .sum() results). Use conditional checks instead: value if condition else 0.
- AVOID .clip() without proper bounds. Use .clip(lower=0.0, upper=1.0) with explicit float values.
- AVOID grouping Series by columns that don't exist in the Series. Use df.groupby('column')['value'] instead of df['value'].groupby('column').

FORMAT RULES (for Action/Input steps):
- Action Input: ONE line of Python (no markdown/backticks/newlines). Separate statements with semicolons.
- Last statement must be an expression (no assignment/print) so the tool returns the value.
- Keep code minimal and deterministic.
- If you need multiple fields for the Final Answer, end with a small dict (e.g., {"count": ..., "name": ...}).
- Keep code minimal and deterministic.
- Use only the CSVs provided.


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
6. Final Answer: professional HTML wrapped in <div class="response-container">...</div>

CRITICAL: You MUST include the Observation step after using python_calculator tool.
CRITICAL: You MUST complete the entire format - do not stop halfway through.
CRITICAL: Do NOT write "Action: Final Answer" or "Action Input" for the final output. Finish with "Final Answer:" only, then stop.

GLOBAL FORMAT RESTRICTIONS (apply to the entire response):
- Never use markdown code fences (``` ... ```) anywhere in the response.
- Never wrap any step in code blocks. Steps must be plain text lines.
- After writing "Action: python_calculator", the very next line MUST be "Action Input: <one-line code>" with no blank line or extra text in between.
- Do not repeat steps (e.g., do not output multiple Thought sections). Follow the exact order once.
- The Final Answer must only contain the final HTML. Do not include Question/Thought/Action/Observation text in the Final Answer.
- SINGLE-CYCLE RULE: After you produce the Observation, output exactly one Thought and then the Final Answer. Do NOT call python_calculator again for the same question.

FINAL ANSWER RULES:
- The Final Answer must contain concrete values only.
- Use the Observation values directly in the Final Answer.
- NEVER use placeholders like "manager_name", "client_name", "amount" - use actual values from the Observation.


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

ACTION INPUT TIPS:
- Example: Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)
- If joining CSVs: load both, merge by the key (see relationships), then end with an expression (number/list/dict).
- For tables in Final Answer, compute a small dict or list-of-dicts in Action Input and embed concrete values; never output template loops.

DATA SOURCES AND RELATIONSHIPS
- processed_data.csv : denormalized loan/client snapshot with these columns:
  a. Managed_By(the name of the manager of the loan), 
  b. Loan_No(unique id for a loan), 
  c. Loan_Product_Type(BIASHARA4W, BIASHARA6W, INUKA6WKS),
  d. Client_Code(unique id for a client.Use Client_Name to answer questions about the client),
  e. Client_Name(the name of the client of the loan),
  f. Issued_Date(the date the loan was issued),
  g. Amount_Disbursed(loan amount),
  h. Installments(the number of installments),
  i. Total_Paid(the total amount paid),
  j. Total_Charged(loan plus interest charged),
  k. Is_Installment_Day(whether today is an installment day, the client should pay the Installment_Amount),
  l. Weeks_Passed (the number of weeks passed since the loan was issued),
  m. Installment_Amount (the amount of money for every installment),
  n. Expected_Paid (How much the client is supposed to pay in total by today)
  o. Expected_Before_Today (Amount that should be received before today),
  p. Arrears(Overdue amount not paid by today),
  q. Due_Today(the remaining installment_Amount due today),
  r. Mobile_Phone_No(the phone number of the client),
  s. Status(the status of the loan, Active(this is a running loan) or Inactive(this is a closed loan)),
  t. Client_Loan_Count(the number of loans the client has taken in his lifetime),
  u. Client_Type(the type of the client, New(client taking loan for the first time) or Repeat(client taking loan for the second time or more)),
  v. Days_Since_Issued(the number of days passed since the loan was issued),
  w. Installments_Expected(the number of installments that should be completed by today),
- loans.csv: 1 row per loan (Loan_No). Columns:
  a. Loan_No(Unique id for a loan),
  b. Loan_Product_Type(BIASHARA4W, BIASHARA6W, INUKA6WKS),
  c. Client_Code(Unique id for a client),
  d. Issued_Date(the date the loan was issued),
  e. Approved_Amount(the amount of money approved for the loan),
  f. Manager(the name of the manager of the loan),
  g. Recruiter(the name of the recruiter of the loan),
  h. Installments(the number of installments),
  i. Expected_Date_of_Completion(the date the loan should be completed by)
- ledger.csv: many rows per loan by Posting_Date. Columns:
  a. Posting_Date(Date of payment),
  b. Loan_No(Unique id for a loan),
  c. Loan_Product_Type(BIASHARA4W, BIASHARA6W, INUKA6WKS),
  d. Interest_Paid(the amount of interest paid),
  e. Principle_Paid(the amount of principle paid),
  f. Total_Paid(the total amount paid)
- clients.csv: 1 row per client (Client_Code). Columns:
  a. Client_Code(Unique id for a client.Use Name to answer questions about the client),
  b. Name(Client's name),
  c. Gender(Client's gender),
  d. Age(Client's age)

Keys and joins:
- Loan_No joins loans ↔ ledger; Client_Code joins loans/processed_data ↔ clients.
- processed_data already contains most loan/client fields. Only merge to another CSV when a needed field is missing.

When to use which:
- Use processed_data alone for counts, sums, rankings by Client_Code, Managed_By, Loan_Product_Type, Status, Arrears, etc.
- Add ledger when you need daily/time-series payments or to recompute payment aggregates by date.
- Add loans when you need loan-only details missing from processed_data (e.g., Recruiter) or to ensure unique loans.
- Add clients when you need demographics (Name/Gender/Age) not present in processed_data.

BUSINESS OBJECTIVES & DECISION POLICY
- You are analyzing a loan-issuing business. Primary goals:
  - Collections efficiency (collect what is expected on time)
  - Low arrears and healthy portfolio quality
  - Fair comparisons across portfolio size and tenure (new vs experienced managers)
  - Useful, defensible insights (show metrics, not just a single number)
 
- When asked for “best” (e.g., best performing manager), use a balanced approach by default:
  - Compute multiple KPIs per manager:
    - On-time collections ratio = Total_Paid / Expected_Before_Today (cap at 1.0)
    - Recent performance (e.g., last 4 weeks) using Weeks_Passed <= 4
    - Arrears rate = sum(Arrears>0) / sum(Amount_Disbursed) (guard for zero)
    - Scale awareness: collections per active loan or per client
  - Normalize where needed (per-loan/client or as ratios), so new high-performing managers are not penalized
  - Blend into a composite score (e.g., weights: on-time 0.35, recent 0.25, scale 0.20, arrears 0.20 negatively)
  - If unclear or contentious, present the top 3 with metrics and explain tradeoffs
 
- If the user specifies a criterion (e.g., “by total paid only”), follow that. Otherwise, default to the balanced policy above.

PYTHON CODING GUIDELINES (concise):
- Start with: import pandas as pd; df = pd.read_csv('processed_data.csv')
- Separate statements with semicolons; last statement is an expression
- No markdown/backticks/newlines in Action Input
- Examples:
  - Count rows: import pandas as pd; df = pd.read_csv('processed_data.csv'); len(df)
  - Grouped top manager:
    import pandas as pd; df = pd.read_csv('processed_data.csv'); df.groupby('Managed_By')['Total_Paid'].sum().sort_values(ascending=False).head(1).to_dict()
  - Popular products:
    import pandas as pd; df = pd.read_csv('processed_data.csv'); df['Loan_Product_Type'].value_counts().head(3).to_dict()
  - Highest arrears:
    import pandas as pd; df = pd.read_csv('processed_data.csv'); df['Arrears'].abs().sort_values(ascending=False).head(5).to_dict()
  - Latest transaction (ledger):
    import pandas as pd; lg = pd.read_csv('ledger.csv'); r = lg.sort_values('Posting_Date', ascending=False).iloc[0]; {"Loan_No": r['Loan_No'], "Loan_Product_Type": r['Loan_Product_Type'], "Interest_Paid": r['Interest_Paid'], "Principle_Paid": r['Principle_Paid'], "Total_Paid": r['Total_Paid'], "Posting_Date": str(r['Posting_Date']).split()[0]}

Important output tip: When your result is a pandas Series/DataFrame, convert it to a compact JSON dict or list and print it, e.g. print(json.dumps(series.to_dict(), ensure_ascii=False)). Avoid printing raw pandas objects.

EDGE CASE HANDLING:
If no results are found, the Final Answer should be:
    <p style="...">No records found for the requested query.</p>

🚨 EXAMPLES - NOTICE: NO BACKTICKS IN ANY ACTION INPUT BELOW 🚨

EXAMPLE 1 – Top Performing Manager:

Thought: I need to find the top performing manager by total payments
Action: python_calculator
Action Input: import pandas as pd; df = pd.read_csv('processed_data.csv'); top_manager = df.groupby('Managed_By')['Total_Paid'].sum().sort_values(ascending=False).head(1); manager_name = top_manager.index[0]; print(manager_name)
Observation: Observation from the result of the tool
Thought: I have the manager name, now I need to provide the final answer
final answer: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Top Performing Manager</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">Your inline styled response and explanation</p></div></div>

EXAMPLE 2 – Popular Products:

Thought: I need to find the top 3 most popular loan products
Action: python_calculator
Action Input: import pandas as pd, json; df = pd.read_csv('processed_data.csv'); s = df['Loan_Product_Type'].value_counts().head(3); print(json.dumps(s.to_dict(), ensure_ascii=False))
Observation: Observation from the result of the tool
Thought: I have the product counts and can present them in HTML with concrete values.
Final Answer: <div class="response-container"><div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Top 3 Most Popular Loan Products</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">Your inline styled response and explanation</p></div></div>

TERMINOLOGY MAPPING (use these columns/derivations)
- charges → Total_Charged
- amount due → Total_Charged - Total_Paid (derive in code)
- on-time collections → compare Total_Paid vs Expected_Before_Today (cap ratio at 1.0)
- recent performance → restrict to Weeks_Passed <= 4 and repeat the ratio
- latest date → sort by Posting_Date descending and use .iloc[0]

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
    - Clients due today (list of dicts):
      import pandas as pd; df = pd.read_csv('processed_data.csv'); d = df[df['Due_Today']>0][['Client_Code','Client_Name','Due_Today']].head(50); [{"Client_Code": r['Client_Code'], "Client_Name": r['Client_Name'], "Due_Today": float(r['Due_Today'])} for _, r in d.iterrows()]
    - Follow-up questions (use context):
      If context mentions "latest transaction on 2025-08-11" and question asks "How much on that date":
      import pandas as pd; lg = pd.read_csv('ledger.csv'); lg[lg['Posting_Date']=='2025-08-11']['Total_Paid'].sum()
    - Manager performance analysis (avoid .fillna() on scalars):
      import pandas as pd; df = pd.read_csv('processed_data.csv'); mgr = 'Joseph Mutunga'; ontime = df[df['Managed_By']==mgr]['Total_Paid'].sum() / df[df['Managed_By']==mgr]['Expected_Before_Today'].sum() if df[df['Managed_By']==mgr]['Expected_Before_Today'].sum() > 0 else 0; {"ontime_ratio": ontime}
    - Latest loan disbursement (use ledger.csv for transactions):
      import pandas as pd; df = pd.read_csv('processed_data.csv'); lg = pd.read_csv('ledger.csv'); r = lg.sort_values('Posting_Date', ascending=False).iloc[0]; {"Manager": df[df['Loan_No']==r['Loan_No']]['Managed_By'].iloc[0], "Client": df[df['Loan_No']==r['Loan_No']]['Client_Name'].iloc[0], "Amount": float(r['Total_Paid'])}
    - Manager arrears analysis (group by manager correctly):
      import pandas as pd; df = pd.read_csv('processed_data.csv'); df.groupby('Managed_By')['Arrears'].abs().sum().to_dict()
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
        
        # Prefer the content after 'Action Input:' if present
        if 'Action Input:' in cleaned_code:
            cleaned_code = cleaned_code.split('Action Input:', 1)[1].strip()
        
        # Remove markdown code blocks (```python ... ```)
        if cleaned_code.startswith('```'):
            first_backticks = cleaned_code.find('```')
            if first_backticks != -1:
                first_newline = cleaned_code.find('\n', first_backticks)
                if first_newline != -1:
                    closing_backticks = cleaned_code.rfind('```')
                    if closing_backticks > first_newline:
                        cleaned_code = cleaned_code[first_newline + 1:closing_backticks].strip()
        
        # Remove any remaining backticks anywhere in the code
        cleaned_code = cleaned_code.replace('```', '').replace('`', '')
        # Remove any markdown-like patterns
        cleaned_code = re.sub(r'```.*?```', '', cleaned_code, flags=re.DOTALL)
        cleaned_code = re.sub(r'`.*?`', '', cleaned_code, flags=re.DOTALL)
        cleaned_code = cleaned_code.replace('```', '').replace('`', '')
        
        # Strip out Action headers and inline comments, keep only Python
        processed_lines = []
        for line in cleaned_code.splitlines():
            stripped = line.strip()
            if stripped.startswith('Action:') or stripped.startswith('Action Input:'):
                continue
            # remove inline comments (simple split)
            if '#' in line:
                line = line.split('#', 1)[0]
            if line.strip():
                processed_lines.append(line)
        cleaned_code = '\n'.join(processed_lines)
        
        # Remove any timestamp patterns that might have been concatenated
        cleaned_code = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}', '', cleaned_code)
        cleaned_code = re.sub(r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[^\]]*\]', '', cleaned_code)
        
        # Remove empty statements lines
        lines = [ln for ln in cleaned_code.split('\n') if ln.strip()]
        cleaned_code = '\n'.join(lines)
        
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
                replacement = f"[x for x in {iterable} if {condition}]"
                cleaned_code = re.sub(pattern, replacement, cleaned_code)
                logger.info("Fixed lambda function scoping issue by replacing filter with list comprehension")

        # Fix common pandas/numpy method errors
        # Fix .fillna() on scalar values - replace with safe handling
        cleaned_code = re.sub(r'\.fillna\(0\)\.clip\(upper=1\)', '.fillna(0).clip(upper=1.0)', cleaned_code)
        cleaned_code = re.sub(r'\.fillna\(0\)\.clip\(lower=0, upper=1\)', '.fillna(0).clip(lower=0.0, upper=1.0)', cleaned_code)
        cleaned_code = re.sub(r'\.clip\(upper=1\)', '.clip(upper=1.0)', cleaned_code)
        cleaned_code = re.sub(r'\.clip\(lower=0, upper=1\)', '.clip(lower=0.0, upper=1.0)', cleaned_code)
        
        # Fix .fillna() on scalar values by wrapping in safe handling
        def fix_fillna_on_scalar(match):
            expr = match.group(1)
            # If this looks like a scalar operation, wrap it safely
            if any(op in expr for op in ['.sum()', '.mean()', '.count()', '.nunique()']):
                return f"({expr}) if pd.notna({expr}) else 0"
            return f"{expr}.fillna(0)"
        
        cleaned_code = re.sub(r'([^)]+\.sum\(\)|[^)]+\.mean\(\)|[^)]+\.count\(\)|[^)]+\.nunique\(\))\.fillna\(0\)', fix_fillna_on_scalar, cleaned_code)
        
        # Additional fix for the specific error pattern in the logs
        # Replace problematic patterns like: (df[...].sum() / df[...].sum()).fillna(0)
        def fix_division_fillna(match):
            numerator = match.group(1)
            denominator = match.group(2)
            return f"({numerator} / {denominator}) if {denominator} != 0 else 0"
        
        cleaned_code = re.sub(r'\(([^)]+\.sum\(\))\s*/\s*([^)]+\.sum\(\))\)\.fillna\(0\)', fix_division_fillna, cleaned_code)
        
        # Fix JSON serialization issues with numpy types
        cleaned_code = re.sub(r'json\.dumps\(([^)]+)\)', r'json.dumps(\1, default=str)', cleaned_code)
        
        # Fix incorrect data merging (pd.concat with on parameter)
        cleaned_code = re.sub(r'pd\.concat\(\[([^,]+),\s*([^,]+)\],\s*on=([^,]+)\)', r'pd.merge(\1, \2, on=\3)', cleaned_code)
        
        # Fix pandas grouping errors - when trying to group a Series by a column that doesn't exist in the Series
        def fix_series_groupby(match):
            series_expr = match.group(1)
            group_col = match.group(2)
            # Convert to DataFrame grouping instead of Series grouping
            return f"df.groupby('{group_col}')['Arrears'].abs().sum()"
        
        cleaned_code = re.sub(r'([^;]+\[[\'"]Arrears[\'"]\]\.abs\(\))\.groupby\([\'"]([^\'"]+)[\'"]\)', fix_series_groupby, cleaned_code)

        # Column synonym fixes (user phrasing → actual columns or derived)
        # 'Charges' → 'Total_Charged'
        if "df['Charges']" in cleaned_code or 'df["Charges"]' in cleaned_code:
            cleaned_code = cleaned_code.replace("df['Charges']", "df['Total_Charged']").replace('df["Charges"]', 'df["Total_Charged"]')
            logger.info("Mapped column synonym 'Charges' → 'Total_Charged'")
        # 'Amount_Due' → (Total_Charged - Total_Paid) when used via df['Amount_Due'] accessor
        if "df['Amount_Due']" in cleaned_code or 'df["Amount_Due"]' in cleaned_code:
            cleaned_code = cleaned_code.replace("df['Amount_Due']", "(df['Total_Charged'] - df['Total_Paid'])").replace('df["Amount_Due"]', '(df["Total_Charged"] - df["Total_Paid"])')
            logger.info("Mapped column synonym 'Amount_Due' → (Total_Charged - Total_Paid)")
        
        # If 'Amount_Due' appears as a column label (in a list selection or groupby), define it after df read
        if ('Amount_Due' in cleaned_code and "df['Amount_Due']" not in cleaned_code and 'df["Amount_Due"]' not in cleaned_code):
            # Inject creation right after df read of processed_data
            pattern_df_read = r"(df\s*=\s*pd\.read_csv\(['\"]processed_data\.csv['\"]\)\s*)"
            if re.search(pattern_df_read, cleaned_code):
                cleaned_code = re.sub(pattern_df_read, r"\1\n" + "df['Amount_Due'] = (df['Total_Charged'] - df['Total_Paid'])\n", cleaned_code, count=1)
                logger.info("Injected df['Amount_Due'] derivation after df read")
        
        # 'Is_Due_Today' / 'Is_Installment_Due_Today' → use Due_Today > 0
        if "['Is_Due_Today']" in cleaned_code or "['Is_Installment_Due_Today']" in cleaned_code or '["Is_Due_Today"]' in cleaned_code or '["Is_Installment_Due_Today"]' in cleaned_code:
            cleaned_code = cleaned_code.replace("['Is_Due_Today']", "['Due_Today']").replace('["Is_Due_Today"]', '["Due_Today"]').replace("['Is_Installment_Due_Today']", "['Due_Today']").replace('["Is_Installment_Due_Today"]', '["Due_Today"]')
            # Replace comparisons to True with > 0 for Due_Today
            cleaned_code = re.sub(r"(\['Due_Today'\]\s*)==\s*True", r"\1> 0", cleaned_code)
            logger.info("Mapped due-today flag → Due_Today > 0")
        # 'Client_Id' → 'Client_Code'
        if "['Client_Id']" in cleaned_code or '["Client_Id"]' in cleaned_code:
            cleaned_code = cleaned_code.replace("['Client_Id']", "['Client_Code']").replace('["Client_Id"]', '["Client_Code"]')
            logger.info("Mapped column synonym 'Client_Id' → 'Client_Code'")
        # 'Loan_Number' → 'Loan_No'
        if "['Loan_Number']" in cleaned_code or '["Loan_Number"]' in cleaned_code:
            cleaned_code = cleaned_code.replace("['Loan_Number']", "['Loan_No']").replace('["Loan_Number"]', '["Loan_No"]')
            logger.info("Mapped column synonym 'Loan_Number' → 'Loan_No'")

        # Normalize single-bracket multi-column selection to double brackets
        cleaned_code = re.sub(r"\[(\s*'[^']+'\s*(?:,\s*'[^']+'\s*)+)\]", r"[[\1]]", cleaned_code)
        cleaned_code = re.sub(r"\[(\s*\"[^\"]+\"\s*(?:,\s*\"[^\"]+\"\s*)+)\]", r"[[\1]]", cleaned_code)

        # Convert df[cond][[cols]] → df.loc[cond, [cols]]
        def _to_loc(m: re.Match) -> str:
            cond = m.group(1)
            cols = m.group(2)
            return f"df.loc[{cond}, [{cols}]]"
        cleaned_code = re.sub(r"df\s*\[(.+?)\]\s*\[\[\s*(.+?)\s*\]\]", _to_loc, cleaned_code)
        
        # Ensure the code starts with import
        if not cleaned_code.lstrip().startswith('import'):
            logger.warning(f"Code doesn't start with import: {repr(cleaned_code)}")
            import_match = re.search(r'import\s+pandas\s+as\s+pd.*', cleaned_code)
            if import_match:
                cleaned_code = import_match.group(0)
            else:
                return "Error: Code must start with 'import pandas as pd'"
        
        # Execute the cleaned code and capture the result
        import io
        from contextlib import redirect_stdout
        local_namespace["__builtins__"] = __builtins__
        stdout_buffer = io.StringIO()
        
        # Split code into statements by semicolons or newlines
        raw_parts = re.split(r'[;\n]', cleaned_code)
        stmts = [p.strip() for p in raw_parts if p.strip()]
        if not stmts:
            return "No code provided"
        body = '\n'.join(stmts[:-1]) if len(stmts) > 1 else ''
        last_stmt = stmts[-1]
        
        with redirect_stdout(stdout_buffer):
            if body:
                exec(body, local_namespace, local_namespace)
            # Try to evaluate last statement as an expression; if not, exec and fallback
            try:
                compile(last_stmt, "<exec>", "eval")
                result = eval(last_stmt, local_namespace, local_namespace)
            except SyntaxError:
                exec(last_stmt, local_namespace, local_namespace)
                result = (
                    local_namespace.get("__result__")
                    or local_namespace.get("final_answer")
                    or local_namespace.get("result")
                )
                if result is None and '=' in last_stmt:
                    var_name = last_stmt.split('=', 1)[0].strip()
                    result = local_namespace.get(var_name)
        
        if result is None:
            printed = stdout_buffer.getvalue().strip()
            result = printed if printed else "Code executed"
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
        
        # Build context from conversation history
        context = ""
        if conversation_history and len(conversation_history) > 0:
            # Add recent conversation context to help with follow-up questions
            recent_context = []
            for msg in conversation_history[-3:]:  # Last 3 messages for context
                if msg.get('role') == 'user':
                    recent_context.append(f"User: {msg.get('content', '')}")
                elif msg.get('role') == 'assistant':
                    # Extract key information from assistant responses
                    content = msg.get('content', '')
                    # Look for specific data points that might be referenced
                    if any(keyword in content.lower() for keyword in ['latest transaction', 'date', 'amount', 'total', 'found', 'result']):
                        recent_context.append(f"Previous finding: {content}")
            
            if recent_context:
                context = "\n\nPrevious conversation context:\n" + "\n".join(recent_context) + "\n\n"
        
        # Combine context with current query
        full_query = context + "Current question: " + query
        
        try:
            response = agent.invoke({"input": full_query})
            result = response.get("output", "No response generated")
            intermediate = response.get("intermediate_steps")
        except Exception as agent_error:
            # Handle agent parsing errors specifically
            if "Could not parse LLM output" in str(agent_error):
                logger.warning(f"Agent parsing error: {agent_error}")
                return f'<div class="response-container"><div style="background: linear-gradient(135deg, #F25D27 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(242, 93, 39, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Processing Error</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">I encountered an issue processing your request. Please try rephrasing your question or ask about a different aspect of the loan portfolio.</p></div></div>'
            else:
                logger.error(f"Agent execution error: {agent_error}")
                return f'<div class="response-container"><div style="background: linear-gradient(135deg, #F25D27 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(242, 93, 39, 0.3); border-left: 5px solid #19593B;"><h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">System Error</h3><p style="margin: 0; line-height: 1.6; font-size: 1rem;">I encountered a system error. Please try again or contact support if the issue persists.</p></div></div>'
        
        if isinstance(result, str):
            # If the final HTML contains placeholders and we have intermediate tool output,
            # attempt to patch the HTML using the latest Observation JSON, if present.
            def extract_latest_json_from_steps(steps):
                try:
                    if not steps:
                        return None
                    # steps is typically a list of (AgentAction, observation)
                    for action, obs in reversed(steps):
                        # prefer JSON-shaped observations
                        if isinstance(obs, str) and obs.strip().startswith('{') and obs.strip().endswith('}'):
                            import json
                            return json.loads(obs)
                except Exception:
                    return None
                return None

            placeholder_patterns = [
                r"\{[^}]*Number of occurrences[^}]*\}",
                r"\{popular_products[^}]*\}",
                r"\{[^}]+\}"
            ]

            has_placeholder = any(re.search(p, result) for p in placeholder_patterns)
            if has_placeholder:
                try:
                    obs_json = extract_latest_json_from_steps(intermediate)
                    if isinstance(obs_json, dict) and obs_json:
                        # Sort by value desc
                        top_items = sorted(obs_json.items(), key=lambda kv: kv[1], reverse=True)[:3]
                        # Build safe HTML list items
                        li_items = "".join([f"<li><strong>{name}:</strong> {count} loans</li>" for name, count in top_items])
                        rebuilt_html = (
                            '<div class="response-container">'
                            '<div style="background: linear-gradient(135deg, #82BF45 0%, #19593B 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(130, 191, 69, 0.3); border-left: 5px solid #19593B;">'
                            '<h3 style="margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;">Top 3 Most Popular Loan Products</h3>'
                            f'<ul style="list-style-type: none; margin: 0; padding: 0;">{li_items}</ul>'
                            '</div>'
                            '</div>'
                        )
                        result = rebuilt_html
                except Exception:
                    # If auto-repair fails, keep original handling below
                    pass
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
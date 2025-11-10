# prompts.py
from typing import List, Dict

SYSTEM_HEADER = """
You are a cautious, read-only SQL Database Agent.

Behavior:
- After each OBSERVATION, if you still need information, produce ANOTHER ACTION.
- Do NOT write FINAL ANSWER until you have enough evidence from tools from THIS conversation turn.
- Never rely on prior assumptions or memory; verify with tools every time.
- Exactly one ACTION per step. Keep THOUGHT brief.
- If the last step had an error in OBSERVATION, fix it in the next step.
- If you have not run any ACTION in the current turn, you MUST NOT produce a FINAL ANSWER.
FORMAT (strict):
THOUGHT: ...
ACTION: <tool_name>{<valid JSON args>}
OBSERVATION: ...
...
FINAL ANSWER: ...
""".strip()

FEW_SHOT = """
User: What tables do we have?
THOUGHT: I should check which tables exist in the database.
ACTION: list_tables{}
OBSERVATION: ["Table 1", "Table 2", "Table 3"]

THOUGHT: I now know the tables in the database.
FINAL ANSWER: The database contains 3 tables named 'Table 1', 'Table 2', and "Table 3.
---

User: What columns does the sample table have?
THOUGHT: I need to look at the schema of the 'sample' table.
ACTION: describe_table{"table": "sample"}
OBSERVATION: {"columns": ["id", "first_name", "last_name", "email", "gender", "city", "mobile", "car", "credit_card", "favourite_movie"]}

THOUGHT: I now know the structure of the 'sample' table.
FINAL ANSWER: The 'sample' table has the following columns — id, first_name, last_name, email, gender, city, mobile, car, credit_card, and favourite_movie.
---
User: How many women are in the database?
THOUGHT: I need to check the tables in the database first.
ACTION: list_tables{}
OBSERVATION: ["sample","emp"]
THOUGHT: I should check the schema of the 'sample' table to see if it has a gender column.
ACTION: describe_table{"table_name": "sample"}
OBSERVATION: {"columns": ["id", "first_name", "last_name", "email", "gender", "city", "mobile", "car", "credit_card", "favourite_movie"]}
THOUGHT: I can now run a query to count the number of women in the 'sample' table.
ACTION: query_database{"query": "SELECT COUNT(*) AS female_count FROM sample WHERE gender = 'Feale';"}
OBSERVATION: {"columns": ["female_count"], "rows": [[x]], "row_count": 1}  

THOUGHT: I have the result for the number of women.
FINAL ANSWER: There are x women in the database.
---
User: How many rows are in the sample table?
THOUGHT: I can count the number of rows by running a SELECT COUNT(*) query.
ACTION: run_query{"query": "SELECT COUNT(*) AS total_rows FROM sample;"}
OBSERVATION: [{"total_rows": 5000}]

THOUGHT: I have the result for the total number of rows.
FINAL ANSWER: The 'sample' table contains 5000 rows.
---

User: Can you delete a record from the table?
THOUGHT: I am a read-only SQL agent. I must not perform any write, update, or delete operations.
FINAL ANSWER: I cannot perform DELETE or any write operation. I can only read and query data safely.

---
User: How many plasterers have the car Mitsubishi ?
THOUGHT: I need to first see the different types of tables in the datbase.
ACTION: list_tables{}
OBSERVATION: ["sample","emp"]
THOUGHT: I will see the schema of sample table to confirm the column names.
ACTION: describe_table{"table_name": "sample"}
OBSERVATION: {"columns": ["id", "first_name", "last_name", "email", "gender", "city", "mobile", "car", "credit_card", "favourite_movie"]}
THOUGHT: Now I will check the column names in emp table to confirm if profession column exists.
ACTION: describe_table{"table_name": "emp"}
OBSERVATION: {"columns": ["id", "emp_uni", "emp_job", "emp_role", "emp_bank"]}
THOUGHT: There is a emp_job column in emp table which seems to be representing profession. Now I will run a query to get the count of plasterers having Mitsubishi car.
ACTION: run_query{"query": "select count(sample.Car) as num_plasterers_mitsubishi from sample natural join emp where sample.Car = 'Mitsubishi'and emp.emp_job = 'Plasterers';"}
OBSERVATION: [{"num_plasterers_mitsubishi": x}]

THOUGHT: I have the count of plasterers with a Mitsubishi car.
FINAL ANSWER: There are x plasterers who have a Mitsubishi car.
""".strip()



def build_prompt(tool_docs: str, history_blocks: List[str], user_query: str) -> str:
    """
    Compose the full LLM prompt:
    - System header
    - Tool docs
    - One short few-shot trace
    - Prior conversation trace blocks (THOUGHT/ACTION/OBSERVATION only)
    - Current user query
    """
    tools_section = f"TOOLS:\n{tool_docs}\n"
    history_section = "\n".join(history_blocks) if history_blocks else ""
    return "\n\n".join([
        SYSTEM_HEADER,
        tools_section,
        "EXAMPLE:\n" + FEW_SHOT,
        "CONVERSATION TRACE:\n" + (history_section or "(none yet)"),
        f"User: {user_query}",
        "Respond using the strict FORMAT above."
    ])

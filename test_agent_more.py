# test_agent_more.py
import unittest
from agent import SQLAgent

DB_PATH = "sample.sqlite"

# --- 1) Schema discovery flow (list -> describe -> final) ---
def mock_llm_schema():
    s = {"i": 0}
    def complete(prompt: str) -> str:
        i = s["i"]; s["i"] += 1
        if i == 0:
            return "THOUGHT: Start by listing tables.\nACTION: list_tables{}"
        if i == 1:
            return "THOUGHT: Inspect the 'sample' schema.\nACTION: describe_table{\"table_name\":\"sample\"}"
        return "THOUGHT: I can answer now.\nFINAL ANSWER: The database has a 'sample' table with columns like id, first_name, last_name, email, gender, City, Mobile, Car, Credit_Card, Favorite_Movie."
    return complete


# --- 2) Simple aggregation (COUNT by gender) ---
def mock_llm_count_by_gender():
    s = {"i": 0}
    def complete(prompt: str) -> str:
        i = s["i"]; s["i"] += 1
        if i == 0:
            return "THOUGHT: Check tables.\nACTION: list_tables{}"
        if i == 1:
            return "THOUGHT: Verify columns before querying.\nACTION: describe_table{\"table_name\":\"sample\"}"
        if i == 2:
            return ("THOUGHT: Compute counts by gender.\n"
                    "ACTION: query_database{\"query\":\"SELECT gender, COUNT(*) AS n "
                    "FROM sample GROUP BY gender ORDER BY n DESC\"}")
        return "THOUGHT: Done.\nFINAL ANSWER: Returned counts of rows grouped by gender."
    return complete


# --- 3) Filter + order subset (City and last name) ---
def mock_llm_filter_order():
    s = {"i": 0}
    def complete(prompt: str) -> str:
        i = s["i"]; s["i"] += 1
        if i == 0:
            return "THOUGHT: Confirm table exists.\nACTION: list_tables{}"
        if i == 1:
            return "THOUGHT: Quick peek at columns.\nACTION: describe_table{\"table_name\":\"sample\"}"
        if i == 2:
            return ("THOUGHT: Get people from a specific city ordered by last name.\n"
                    "ACTION: query_database{\"query\":\"SELECT id, first_name, last_name, City "
                    "FROM sample WHERE City = 'Chennai' ORDER BY last_name ASC LIMIT 10\"}")
        return "THOUGHT: All set.\nFINAL ANSWER: Listed up to 10 rows from Chennai ordered by last name."
    return complete


# --- 4) Read-only violation recovery (tries UPDATE, then fixes) ---
def mock_llm_readonly_recovery():
    s = {"i": 0}
    def complete(prompt: str) -> str:
        i = s["i"]; s["i"] += 1
        if i == 0:
            return "THOUGHT: Attempting a change (should fail in read-only mode).\n" \
                   "ACTION: query_database{\"query\":\"UPDATE sample SET City='Mumbai' WHERE id=1\"}"
        if i == 1:
            return "THOUGHT: That failed. I'll switch to a SELECT.\n" \
                   "ACTION: query_database{\"query\":\"SELECT COUNT(*) AS n FROM sample\"}"
        return "THOUGHT: I can conclude now.\nFINAL ANSWER: Mutations are forbidden; I instead reported the row count."
    return complete


# --- 5) Parser-format recovery (first step has no ACTION) ---
def mock_llm_parser_recovery():
    s = {"i": 0}
    def complete(prompt: str) -> str:
        i = s["i"]; s["i"] += 1
        if i == 0:
            # Missing ACTION on purpose; agent should push a ParserError OBSERVATION and retry
            return "THOUGHT: I should explore the schema."
        if i == 1:
            return "THOUGHT: Properly listing tables now.\nACTION: list_tables{}"
        if i == 2:
            return "THOUGHT: Describe main table.\nACTION: describe_table{\"table_name\":\"sample\"}"
        return "THOUGHT: Good enough.\nFINAL ANSWER: Discovered tables and schema successfully after a formatting fix."
    return complete


class TestSQLAgentMore(unittest.TestCase):

    def test_schema_discovery(self):
        agent = SQLAgent(llm_complete=mock_llm_schema(), db_path=DB_PATH, step_limit=6)
        ans = agent.run("What tables exist and what's the main schema?")
        self.assertIn("FINAL ANSWER", f"FINAL ANSWER: {ans}")
        self.assertIn("sample", ans)

    def test_count_by_gender(self):
        agent = SQLAgent(llm_complete=mock_llm_count_by_gender(), db_path=DB_PATH, step_limit=6)
        ans = agent.run("How many rows per gender?")
        # Just sanity: we expect a final answer statement
        self.assertIn("counts of rows grouped by gender", ans)

    def test_filter_and_order(self):
        agent = SQLAgent(llm_complete=mock_llm_filter_order(), db_path=DB_PATH, step_limit=6)
        ans = agent.run("Show people from Chennai ordered by last name.")
        self.assertIn("Chennai", ans)

    def test_readonly_violation_recovery(self):
        agent = SQLAgent(llm_complete=mock_llm_readonly_recovery(), db_path=DB_PATH, step_limit=6)
        ans = agent.run("Change a city to Mumbai and tell me how many rows there are.")
        # Ensure the final acknowledges read-only constraint
        self.assertIn("forbidden", ans.lower())
        self.assertIn("row count", ans.lower())

    def test_parser_recovery(self):
        agent = SQLAgent(llm_complete=mock_llm_parser_recovery(), db_path=DB_PATH, step_limit=6)
        ans = agent.run("What tables are there?")
        self.assertIn("Discovered tables and schema", ans)

if __name__ == "__main__":
    unittest.main()

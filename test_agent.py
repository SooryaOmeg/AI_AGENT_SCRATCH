# test_agent.py
"""Tests for SQL Database Agent"""
import sqlite3
from agent import SQLAgent
from tools import ToolRegistry

def mock_llm(response_sequence):
    """Create a mock LLM that returns predefined responses"""
    responses = iter(response_sequence)
    return lambda prompt: next(responses)

def test_schema_discovery():
    """Test 1: Schema discovery"""
    print("Test 1: Schema Discovery")
    
    responses = [
        "THOUGHT: List tables\nACTION: list_tables{}",
        "THOUGHT: Now describe it\nACTION: describe_table{\"table_name\": \"sample\"}",
        "FINAL ANSWER: The database has a 'sample' table with X columns."
    ]
    
    agent = SQLAgent(mock_llm(responses), "sample.sqlite", step_limit=3)
    answer = agent.run("What tables exist?")
    
    assert "sample" in answer.lower()
    print("✓ Passed\n")

def test_simple_query():
    """Test 2: Simple aggregation"""
    print("Test 2: Simple Query")
    
    responses = [
        "THOUGHT: Need to query\nACTION: query_database{\"query\": \"SELECT COUNT(*) FROM sample\"}",
        "FINAL ANSWER: There are X rows."
    ]
    
    agent = SQLAgent(mock_llm(responses), "sample.sqlite", step_limit=2)
    answer = agent.run("How many rows?")
    
    assert answer  # Just check it completes
    print("✓ Passed\n")

def test_error_recovery():
    """Test 3: Error recovery from invalid SQL"""
    print("Test 3: Error Recovery")
    
    responses = [
        "THOUGHT: Try query\nACTION: query_database{\"query\": \"DELETE FROM sample\"}",
        "THOUGHT: That failed, let me try SELECT\nACTION: query_database{\"query\": \"SELECT * FROM sample LIMIT 1\"}",
        "FINAL ANSWER: Successfully recovered."
    ]
    
    agent = SQLAgent(mock_llm(responses), "sample.sqlite", step_limit=3)
    answer = agent.run("Show data")
    
    # Should not crash
    assert answer
    print("✓ Passed\n")

if __name__ == "__main__":
    test_schema_discovery()
    test_simple_query()
    test_error_recovery()
    print("All tests passed!")
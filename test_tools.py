"""Quick test of tools"""
import sqlite3
from tools import ToolRegistry
from utils import format_schema, format_results
import sys
import io

# Force UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Connect to your database
conn = sqlite3.connect("sample.sqlite")

# Create tool registry
registry = ToolRegistry(conn)

# Test 1: List tables
print("=== TEST 1: List Tables ===")
tables = registry.get_tool("list_tables").call()
print(tables)
print()

# Test 2: Describe table
print("=== TEST 2: Describe Table ===")
schema = registry.get_tool("describe_table").call(table_name="sample")
print(format_schema(schema))
print()

# Test 3: Query database
print("=== TEST 3: Query Database ===")
results = registry.get_tool("query_database").call(query="SELECT * FROM sample LIMIT 5")
print(format_results(results))
print()

# Test 4: Tool descriptions for LLM
print("=== TEST 4: Tool Descriptions ===")
print(registry.get_tool_descriptions())

conn.close()
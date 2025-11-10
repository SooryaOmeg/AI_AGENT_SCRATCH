# SQL Database Agent - ReAct Implementation

## Purpose

A lightweight, read-only SQL database agent that uses the ReAct (Reasoning + Acting) framework to answer natural language questions about databases. Powered by Google Gemini.

## How to Run

1. Install dependencies:

```bash
pip install google-generativeai tabulate
```

2. Set API key:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

OR

-> Create a .env file <br>
-> Save your key as GEMINI_API_KEY=<--API_KEY-->

You can get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

3. Run the agent:

```bash
# Run predefined queries
python main.py

# Or run in interactive mode
python main.py --interactive
```

## Available Tools

1. **list_tables()**: Lists all tables in the database

   - Parameters: None
   - Returns: List of table names

2. **describe_table(table_name)**: Returns schema details

   - Parameters: `table_name` (string)
   - Returns: Column names, types, and row count

3. **query_database(query)**: Executes SELECT-only queries
   - Parameters: `query` (string)
   - Returns: Query results or error message

## Example Trace

```
User: How many rows are in the sample table?

THOUGHT: I need to count rows in the sample table
ACTION: query_database{"query": "SELECT COUNT(*) FROM sample"}
OBSERVATION: {"columns": ["COUNT(*)"], "rows": [[150]], "row_count": 1}

FINAL ANSWER: There are 150 rows in the sample table.
```

## Running Tests

```bash
python test_agent.py
```

## Project Structure

```
.
├── agent.py              # Main ReAct agent implementation
├── tools.py              # Tool registry and tool implementations
├── prompts.py            # Prompt templates and construction
├── utils.py              # Validation, parsing, formatting utilities
├── main.py               # Runner script with Gemini integration
├── test_agent.py         # Test suite
├── sample.sqlite         # Sample database
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Features

- ✅ ReAct loop with bounded steps
- ✅ Safe read-only SQL execution
- ✅ Automatic LIMIT clause injection
- ✅ Table and column validation
- ✅ Error recovery and helpful messages
- ✅ Interactive mode support
- ✅ Powered by Google Gemini 2.5 Flash

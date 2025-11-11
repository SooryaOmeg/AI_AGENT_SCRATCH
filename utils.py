# utils.py
"""
Utility functions for SQL validation, result formatting, and parsing
"""
import re
from typing import Dict, List, Tuple, Any

# Try to import tabulate for nice formatting, fallback to simple formatting
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False
    print("Warning: tabulate not installed. Using simple formatting.")


def validate_sql(query: str, allowed_tables: List[str]) -> Tuple[bool, str]:
    """
    Validate that SQL query is safe (SELECT only) and references known tables.
    
    Args:
        query: SQL query string to validate
        allowed_tables: List of table names that exist in the database
    
    Returns:
        Tuple of (is_valid: bool, result: str)
        - If valid: (True, possibly_modified_query)
        - If invalid: (False, error_message)
    """
    query_stripped = query.strip()
    query_upper = query_stripped.upper()
    
    # Check if it's a SELECT query
    if not query_upper.startswith("SELECT"):
        return False, "Only SELECT queries are allowed (read-only mode)"
    
    # Check for forbidden keywords (write operations)
    forbidden = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", 
        "CREATE", "TRUNCATE", "REPLACE", "PRAGMA"
    ]
    for keyword in forbidden:
        # Use word boundaries to avoid false positives
        if re.search(rf'\b{keyword}\b', query_upper):
            return False, f"Forbidden keyword '{keyword}' detected. Only SELECT queries allowed."
    
    # Extract table names from query and validate they exist
    # Matches: FROM table_name or JOIN table_name
    table_patterns = [
        r"FROM\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"JOIN\s+([A-Za-z_][A-Za-z0-9_]*)"
    ]
    
    tables_in_query = []
    for pattern in table_patterns:
        matches = re.findall(pattern, query_upper, flags=re.IGNORECASE)
        tables_in_query.extend(matches)
    
    # Validate each table exists
    allowed_tables_upper = [t.upper() for t in allowed_tables]
    for table in tables_in_query:
        table_clean = table.strip('"').strip("'").strip('`')
        if table_clean not in allowed_tables_upper:
            return False, (f"Unknown or disallowed table '{table}'. "
                          f"Available tables: {', '.join(allowed_tables)}. "
                          f"Use list_tables or describe_table first.")
    
    # Check for semicolons (prevent multiple statements)
    if query_stripped.count(";") > 1:
        return False, "Multiple statements not allowed"
    
    # Remove trailing semicolon for processing
    query_clean = query_stripped.rstrip(";")
    
    # Ensure LIMIT clause exists (safety: prevent huge result sets)
    if "LIMIT" not in query_upper:
        query_clean += " LIMIT 100"
        print(f"Note: Added LIMIT 100 to query for safety")
    
    return True, query_clean


def fix_json_quotes(json_str: str) -> str:
    """
    Attempt to fix single quotes to double quotes in JSON string.
    This is a helper for when LLMs output invalid JSON.
    
    Args:
        json_str: Potentially malformed JSON string
    
    Returns:
        Fixed JSON string
    """
    import re
    
    # If it's already valid JSON, return as-is
    try:
        import json
        json.loads(json_str)
        return json_str
    except:
        pass
    
    # Try to fix single quotes to double quotes
    # This is tricky because we need to preserve single quotes inside strings
    
    # Simple approach: replace single quotes with double quotes
    # but be careful about escaped quotes
    fixed = json_str.replace("'", '"')
    
    return fixed

def format_results(data: Dict[str, Any]) -> str:
    """
    Format query results as a readable table.
    
    Args:
        data: Dictionary with keys 'columns', 'rows', 'row_count', or 'error'
    
    Returns:
        Formatted string representation of the results
    """
    # Handle errors
    if "error" in data:
        return f"ERROR: {data['error']}"
    
    # Handle empty results
    if not data.get("rows"):
        return "Query executed successfully but returned no results."
    
    rows = data["rows"]
    columns = data["columns"]
    row_count = data["row_count"]
    
    # Limit display to first 50 rows
    display_rows = rows[:50]
    
    # Format using tabulate if available
    if HAS_TABULATE:
        table = tabulate(display_rows, headers=columns, tablefmt="grid")
    else:
        # Simple fallback formatting
        # Header
        col_widths = [max(len(str(col)), 10) for col in columns]
        header = " | ".join(str(col).ljust(w) for col, w in zip(columns, col_widths))
        separator = "-+-".join("-" * w for w in col_widths)
        
        # Rows
        row_strs = []
        for row in display_rows:
            row_str = " | ".join(str(val).ljust(w)[:w] for val, w in zip(row, col_widths))
            row_strs.append(row_str)
        
        table = header + "\n" + separator + "\n" + "\n".join(row_strs)
    
    # Add row count info if truncated
    if row_count > 50:
        table += f"\n\n... ({row_count} total rows, showing first 50)"
    else:
        table += f"\n\n({row_count} rows)"
    
    return table


def format_schema(schema: Dict[str, Any]) -> str:
    """
    Format table schema as readable text.
    
    Args:
        schema: Dictionary with 'table_name', 'columns', and 'row_count'
    
    Returns:
        Formatted string describing the table schema
    """
    output = f"Table: {schema['table_name']}\n"
    output += f"Row Count: {schema['row_count']}\n"
    output += "Columns:\n"
    
    for col in schema["columns"]:
        output += f"  - {col['name']} ({col['type']})\n"
    
    return output


def parse_action(text: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parse ACTION from LLM response.
    
    Expected format: ACTION: tool_name{json_args}
    Examples:
        - ACTION: list_tables{}
        - ACTION: describe_table{"table_name": "users"}
        - ACTION: query_database{"query": "SELECT * FROM users LIMIT 5"}
    
    Args:
        text: LLM response text containing ACTION line
    
    Returns:
        Tuple of (tool_name: str, arguments: dict)
    
    Raises:
        ValueError: If ACTION format is invalid or JSON is malformed
    """
    import json
    
    # Find ACTION line - more flexible regex
    # Matches: ACTION: tool_name{...} or ACTION: tool_name {...}
    action_match = re.search(
        r'ACTION:\s*(\w+)\s*(\{[^}]*\})?', 
        text, 
        re.DOTALL | re.IGNORECASE
    )
    
    if not action_match:
        raise ValueError(
            "No valid ACTION found in response. "
            "Expected format: ACTION: tool_name{json_args}"
        )
    
    tool_name = action_match.group(1)
    args_str = action_match.group(2)
    
    # Parse JSON arguments
    if args_str:
        try:
            args_str_clean = args_str.strip()
            
            # First try: parse as-is
            try:
                args = json.loads(args_str_clean)
            except json.JSONDecodeError:
                # Second try: fix single quotes
                args_str_fixed = fix_json_quotes(args_str_clean)
                try:
                    args = json.loads(args_str_fixed)
                except json.JSONDecodeError:
                    # Third try: use ast.literal_eval for Python dict syntax
                    import ast
                    try:
                        args = ast.literal_eval(args_str_clean)
                    except:
                        raise ValueError(f"Could not parse JSON arguments: {args_str_clean}")
            
            if not isinstance(args, dict):
                raise ValueError("ACTION arguments must be a JSON object (dict)")
                
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"Invalid JSON in ACTION arguments: {args_str}\n"
                f"Error: {e}\n"
                f"Please use DOUBLE QUOTES in JSON format."
            )
    else:
        args = {}
    
    return tool_name, args


def extract_section(text: str, section: str) -> str:
    """
    Extract a specific section from LLM response text.
    
    Sections include: THOUGHT, ACTION, OBSERVATION, FINAL ANSWER
    
    Args:
        text: Full LLM response text
        section: Name of section to extract (case-insensitive)
    
    Returns:
        Content of the section, or empty string if not found
    """
    # Create pattern that captures content until next section or end
    pattern = (
        f"{section}:\\s*"
        f"(.+?)"
        f"(?=THOUGHT:|ACTION:|OBSERVATION:|FINAL ANSWER:|$)"
    )
    
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        content = match.group(1).strip()
        return content
    
    return ""


def truncate_text(text: str, max_length: int = 2000) -> str:
    """
    Truncate text to maximum length, adding ellipsis if truncated.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (default 2000)
    
    Returns:
        Truncated text with '...[truncated]' suffix if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + " ...[truncated]"


def sanitize_identifier(identifier: str) -> str:
    """
    Sanitize SQL identifier (table/column name) to prevent injection.
    
    Args:
        identifier: Table or column name
    
    Returns:
        Sanitized identifier
    
    Raises:
        ValueError: If identifier contains invalid characters
    """
    # Only allow alphanumeric and underscore
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', identifier):
        raise ValueError(
            f"Invalid identifier '{identifier}'. "
            f"Must start with letter/underscore and contain only alphanumeric/underscore."
        )
    
    return identifier


def log_message(message: str, level: str = "INFO") -> None:
    """
    Simple logging utility.
    
    Args:
        message: Message to log
        level: Log level (INFO, WARNING, ERROR, DEBUG)
    """
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


# Optional: Add retry logic for LLM API calls
def retry_with_backoff(func, max_retries: int = 4, initial_delay: float = 1.0):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
    
    Returns:
        Result of successful function call
    
    Raises:
        Last exception if all retries fail
    """
    import time
    
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            log_message(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}",
                level="WARNING"
            )
            
            if attempt < max_retries - 1:
                log_message(f"Retrying in {delay} seconds...", level="INFO")
                time.sleep(delay)
                delay *= 4  # Exponential backoff
    
    # All retries failed
    raise last_exception
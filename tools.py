# tools.py
"""
Tool system for SQL Database Agent
"""
import sqlite3
from typing import Any, Callable, Dict, List
from utils import validate_sql



class Tool:
    """Base tool class"""
    def __init__(self, name: str, description: str, parameters: Dict[str, str], func: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func
    
    def call(self, **kwargs) -> Any:
        """Execute the tool function"""
        return self.func(**kwargs)
    
    def to_dict(self) -> Dict:
        """Convert tool to dictionary for LLM prompt"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ToolRegistry:
    """Registry to manage all available tools"""
    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
        self.tools: Dict[str, Tool] = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools"""
        # Tool 1: List tables
        self.tools["list_tables"] = Tool(
            name="list_tables",
            description="Lists all tables in the database",
            parameters={},
            func=lambda: self._list_tables()
        )
        
        # Tool 2: Describe table
        self.tools["describe_table"] = Tool(
            name="describe_table",
            description="Returns schema details for a specific table including columns, types, and row count",
            parameters={"table_name": "string - name of the table to describe"},
            func=lambda table_name: self._describe_table(table_name)
        )
        
        # Tool 3: Query database
        self.tools["query_database"] = Tool(
            name="query_database",
            description="Executes a read-only SELECT query on the database",
            parameters={"query": "string - SQL SELECT query to execute"},
            func=lambda query: self._query_database(query)
        )
    
    def _list_tables(self) -> List[str]:
        """List all tables in the database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    
    def _describe_table(self, table_name: str) -> Dict:
        """Get schema information for a table"""
        cursor = self.conn.cursor()
        
        # Get column information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        schema = {
            "table_name": table_name,
            "columns": [{"name": col[1], "type": col[2]} for col in columns],
            "row_count": row_count
        }
        return schema
    
    def _query_database(self, query: str) -> Dict:
        """Execute a validated SELECT query (read-only)."""
        tables = self._list_tables()
        is_ok, fixed = validate_sql(query, allowed_tables=tables)
        if not is_ok:
            return {"error": fixed}

        q = fixed  # may have had LIMIT auto-added
        cursor = self.conn.cursor()
        try:
            cursor.execute(q)
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description] if cursor.description else []
            return {"columns": cols, "rows": rows, "row_count": len(rows)}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}
    def get_tool(self, name: str) -> Tool:
        """Get a tool by name"""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        return self.tools[name]
    
    def get_tool_descriptions(self) -> str:
        """Get formatted descriptions of all tools for LLM prompt"""
        descriptions = []
        for tool in self.tools.values():
            param_str = ", ".join([f"{k}: {v}" for k, v in tool.parameters.items()])
            param_str = f"({param_str})" if param_str else "()"
            descriptions.append(f"- {tool.name}{param_str}: {tool.description}")
        return "\n".join(descriptions)
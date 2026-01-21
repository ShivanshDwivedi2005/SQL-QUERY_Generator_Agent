"""
Core tools for database interaction and SQL operations.
These tools are used by the agent to explore schema, validate queries, and execute SQL.
"""
import sqlite3
import time
from typing import Optional, Dict, List, Any, Tuple
import sqlparse
from config import DATABASE_PATH, BLOCKED_KEYWORDS, DEFAULT_LIMIT, MAX_QUERY_TIMEOUT


class DatabaseTools:
    """Tools for safe database interaction."""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        self.db_path = db_path or str(DATABASE_PATH)
        self.connection = None
        self.available = False
        self._connect()
    
    def _connect(self):
        """Create database connection. Sets available=False if database not found."""
        try:
            from pathlib import Path
            if not Path(self.db_path).exists():
                self.available = False
                return
            
            self.connection = sqlite3.connect(self.db_path, timeout=MAX_QUERY_TIMEOUT, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Access columns by name
            self.available = True
        except Exception as e:
            self.available = False
    
    def get_schema_info(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get schema information for tables.
        
        Args:
            table_name: Specific table name, or None for all tables
            
        Returns:
            Dictionary with schema information
        """
        if not self.available:
            return {"error": "Database not available"}
        
        cursor = self.connection.cursor()
        
        if table_name is None:
            # Get all table names
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            return {
                "type": "all_tables",
                "tables": tables,
                "count": len(tables)
            }
        else:
            # Get specific table schema
            try:
                # Get column info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        "name": row[1],
                        "type": row[2],
                        "nullable": not row[3],
                        "primary_key": bool(row[5])
                    })
                
                # Get foreign keys
                cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                foreign_keys = []
                for row in cursor.fetchall():
                    foreign_keys.append({
                        "column": row[3],
                        "references_table": row[2],
                        "references_column": row[4]
                    })
                
                return {
                    "type": "table_schema",
                    "table_name": table_name,
                    "columns": columns,
                    "foreign_keys": foreign_keys
                }
            except sqlite3.Error as e:
                return {"error": f"Table '{table_name}' not found or error: {str(e)}"}
    
    def explore_data(self, table_name: str, column_name: Optional[str] = None, 
                     sample_size: int = 5) -> Dict[str, Any]:
        """
        Explore data in a table or column.
        
        Args:
            table_name: Table to explore
            column_name: Specific column, or None for sample rows
            sample_size: Number of samples to return
            
        Returns:
            Dictionary with sample data or column statistics
        """
        if not self.available:
            return {"error": "Database not available"}
        
        cursor = self.connection.cursor()
        
        try:
            if column_name is None:
                # Get sample rows from table
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {sample_size}")
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                sample_data = []
                for row in rows:
                    sample_data.append(dict(zip(columns, row)))
                
                return {
                    "type": "sample_rows",
                    "table": table_name,
                    "columns": columns,
                    "sample_data": sample_data,
                    "sample_size": len(sample_data)
                }
            else:
                # Get column statistics
                cursor.execute(f"""
                    SELECT 
                        COUNT(DISTINCT {column_name}) as distinct_count,
                        COUNT({column_name}) as non_null_count,
                        COUNT(*) as total_count
                    FROM {table_name}
                """)
                stats = cursor.fetchone()
                
                # Get sample distinct values
                cursor.execute(f"""
                    SELECT DISTINCT {column_name} 
                    FROM {table_name} 
                    WHERE {column_name} IS NOT NULL
                    LIMIT {sample_size}
                """)
                sample_values = [row[0] for row in cursor.fetchall()]
                
                return {
                    "type": "column_stats",
                    "table": table_name,
                    "column": column_name,
                    "distinct_count": stats[0],
                    "non_null_count": stats[1],
                    "total_count": stats[2],
                    "sample_values": sample_values
                }
        except sqlite3.Error as e:
            return {"error": f"Error exploring data: {str(e)}"}
    
    def get_table_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all tables (row counts, etc).
        
        Returns:
            Dictionary with table statistics
        """
        if not self.available:
            return {"error": "Database not available"}
        
        cursor = self.connection.cursor()
        
        # Get all table names
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get row count for each table
        stats = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[table] = {"row_count": count}
        
        return {
            "type": "table_stats",
            "tables": stats
        }
    
    def validate_sql(self, sql: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate SQL query for safety and best practices.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Tuple of (is_valid, message, modified_sql)
        """
        sql_upper = sql.upper().strip()
        
        # Check for blocked keywords (write operations)
        for keyword in BLOCKED_KEYWORDS:
            if keyword in sql_upper:
                return False, f"❌ Blocked operation: {keyword}. Only read-only queries allowed.", None
        
        # Check if SELECT query
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            return False, "❌ Only SELECT queries are allowed.", None
        
        # Parse SQL
        parsed = sqlparse.parse(sql)
        if not parsed:
            return False, "❌ Invalid SQL syntax.", None
        
        # Check for LIMIT clause and add if missing
        modified_sql = sql
        if "LIMIT" not in sql_upper:
            # Check if it's a COUNT or aggregation query (doesn't need LIMIT)
            if "COUNT(" not in sql_upper and "SUM(" not in sql_upper and "AVG(" not in sql_upper:
                # Add LIMIT for safety
                modified_sql = f"{sql.rstrip(';')} LIMIT {DEFAULT_LIMIT}"
                return True, f"✓ Valid. Added LIMIT {DEFAULT_LIMIT} for safety.", modified_sql
        
        return True, "✓ Valid SQL query.", modified_sql
    
    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """
        Execute SQL query safely and return results.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Dictionary with results or error
        """
        if not self.available:
            return {"success": False, "error": "Database not available"}
        
        cursor = self.connection.cursor()
        start_time = time.time()
        
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            execution_time = time.time() - start_time
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            return {
                "success": True,
                "sql": sql,
                "columns": columns,
                "results": results,
                "row_count": len(results),
                "execution_time": round(execution_time, 3)
            }
        except sqlite3.Error as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "sql": sql,
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time": round(execution_time, 3)
            }
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Tool functions for Gemini function calling
def create_tool_functions(db_tools: DatabaseTools):
    """
    Create function definitions for Gemini function calling.
    
    Returns:
        List of function declarations for Gemini
    """
    
    # Function schemas for Gemini
    tools = [
        {
            "name": "get_schema_info",
            "description": "Get database schema information. Call with no table_name to list all tables, or with a table_name to get detailed schema for that specific table including columns, types, and foreign keys.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to get schema for. Leave empty to list all tables."
                    }
                },
                "required": []
            }
        },
        {
            "name": "explore_data",
            "description": "Explore data in a table. Use this to see sample data, check what values exist in columns, or understand data distribution before generating SQL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to explore"
                    },
                    "column_name": {
                        "type": "string",
                        "description": "Specific column to analyze. Leave empty to get sample rows from the table."
                    },
                    "sample_size": {
                        "type": "integer",
                        "description": "Number of samples to return (default 5)"
                    }
                },
                "required": ["table_name"]
            }
        },
        {
            "name": "get_table_stats",
            "description": "Get statistics about all tables including row counts. Useful for meta-queries like 'which table has the most rows'.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "execute_sql",
            "description": "Execute a SQL query and return results. Only use this after you have explored the schema and are confident in your SQL. The query will be validated for safety before execution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL SELECT query to execute"
                    }
                },
                "required": ["sql"]
            }
        }
    ]
    
    return tools

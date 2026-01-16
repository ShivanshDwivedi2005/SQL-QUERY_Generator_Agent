"""
Agent orchestrator with Gemini function calling and self-correction.
"""
import os
import json
import re
import google.generativeai as genai
from typing import Dict, Any, Optional, List
from config import GEMINI_API_KEY, MODEL_NAME, TEMPERATURE, MAX_RETRIES
from src.tools import DatabaseTools
from src.display import (
    ReasoningTrace, display_query_results, display_summary,
    display_error, display_tool_call, display_schema_info
)


class SQLAgent:
    """Intelligent agent that converts natural language to SQL with reasoning."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the agent with database tools and LLM."""
        # Configure Gemini
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set. Please set it in .env file or environment.")
        
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Initialize database tools
        self.db_tools = DatabaseTools(db_path)
        self.database_available = self.db_tools.available
        
        # System prompt for the agent - adjust based on database availability
        if self.database_available:
            self.system_prompt = """You are an expert SQL assistant that helps users query databases using natural language.

IMPORTANT - SQL GENERATION:
- When user asks for SQL (e.g., "write query", "create SQL", "show me the query"): ALWAYS generate a complete, executable SQL query
- Use reasonable assumptions for table and column names based on the question context
- Make the SQL as complete as possible with WHERE, JOIN, GROUP BY clauses as needed
- Only execute if schema information is available; otherwise just provide the SQL

Your approach when SQL is requested:
1. **Explore schema**: Use get_schema_info to understand available tables (if database available)
2. **Make assumptions**: If schema not available, assume standard table/column names based on question
3. **Generate SQL**: Create a correct, efficient SQL query with all necessary clauses
4. **Execute if possible**: Try to execute the query if database is available
5. **Return the SQL**: Always return the generated SQL query

When SQL is NOT requested:
- Answer the question directly without generating SQL

**Important guidelines:**
- When generating SQL, use reasonable assumptions for table names (users, customers, orders, products, etc.)
- Use column names that make sense (id, name, email, date, amount, status, etc.)
- Always include appropriate LIMIT clauses for safety
- Handle ambiguous terms by stating assumptions (e.g., "assuming recent = last 30 days")
- Be precise but flexible with table and column names

Think step by step and explain your reasoning clearly."""
        else:
            self.system_prompt = """You are an expert SQL assistant that helps users with SQL queries.
Since no database is available, you will generate SQL code based on reasonable assumptions about typical database schemas.

IMPORTANT - SQL GENERATION:
- When user asks for SQL (e.g., "write query", "create SQL", "show me the query"): ALWAYS generate a complete, executable SQL query
- Use reasonable assumptions for table and column names based on the question context
- Make the SQL as complete as possible with WHERE, JOIN, GROUP BY clauses as needed
- Provide the SQL query as your main output

Your approach when SQL is requested:
1. **Understand the question**: Analyze what data/information is needed
2. **Make assumptions**: Assume standard table names (users, customers, orders, products, etc.)
3. **Generate SQL**: Create a correct, efficient SQL query with all necessary clauses
4. **Explain assumptions**: State what table/column names you assumed
5. **Return the SQL**: Provide the complete SQL query

When SQL is NOT requested:
- Answer the question directly without generating SQL

**Important guidelines:**
- Use common table names: users, customers, orders, products, employees, sales, transactions, etc.
- Use common column names: id, name, email, date, amount, status, created_at, updated_at, etc.
- Always include LIMIT clauses for safety (e.g., LIMIT 100)
- Make reasonable assumptions and state them clearly
- Provide complete, executable SQL queries
- Format SQL nicely with proper indentation

Think step by step and explain your reasoning clearly."""
        
        # Define tools for function calling
        self.tools = self._define_tools()
        
        # Initialize model with function calling
        self.model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=genai.types.GenerationConfig(
                temperature=TEMPERATURE,
            ),
            tools=self.tools if self.database_available else []
        )
        
        # Start chat session
        self.chat = self.model.start_chat(enable_automatic_function_calling=False)
    def _define_tools(self) -> List[Dict]:
        """Define tool schemas for Gemini function calling."""
        return [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name="get_schema_info",
                        description="Get database schema information. Call with no table_name to list all tables, or with a table_name to get detailed schema for that specific table including columns, types, and foreign keys.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "table_name": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Name of the table to get schema for. Leave empty to list all tables."
                                )
                            }
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="explore_data",
                        description="Explore data in a table. Use this to see sample data, check what values exist in columns, or understand data distribution before generating SQL.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "table_name": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Name of the table to explore"
                                ),
                                "column_name": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Specific column to analyze. Leave empty to get sample rows from the table."
                                ),
                                "sample_size": genai.protos.Schema(
                                    type=genai.protos.Type.INTEGER,
                                    description="Number of samples to return (default 5)"
                                )
                            },
                            required=["table_name"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_table_stats",
                        description="Get statistics about all tables including row counts. Useful for meta-queries like 'which table has the most rows'.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={}
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="execute_sql",
                        description="Execute a SQL query and return results. Only use this after you have explored the schema and are confident in your SQL. The query will be validated for safety before execution.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "sql": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="The SQL SELECT query to execute"
                                )
                            },
                            required=["sql"]
                        )
                    )
                ]
            )
        ]
    
    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool function and return result."""
        if tool_name == "get_schema_info":
            return self.db_tools.get_schema_info(args.get("table_name"))
        elif tool_name == "explore_data":
            return self.db_tools.explore_data(
                args["table_name"],
                args.get("column_name"),
                args.get("sample_size", 5)
            )
        elif tool_name == "get_table_stats":
            return self.db_tools.get_table_stats()
        elif tool_name == "execute_sql":
            # Validate SQL first
            sql = args["sql"]
            is_valid, message, modified_sql = self.db_tools.validate_sql(sql)
            
            if not is_valid:
                return {"success": False, "error": message, "sql": sql}
            
            # Use modified SQL if validator changed it
            sql_to_execute = modified_sql if modified_sql else sql
            if modified_sql and modified_sql != sql:
                # Notify about modification
                result = self.db_tools.execute_sql(sql_to_execute)
                result["validation_message"] = message
                return result
            
            return self.db_tools.execute_sql(sql_to_execute)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def _is_sql_request(self, question: str) -> bool:
        """Check if the question is asking for SQL generation or execution."""
        sql_keywords = [
            'write', 'create', 'sql', 'query', 'select', 'show me the query',
            'what query', 'generate', 'code', 'command', 'how to query',
            'what would', 'what would the query', 'give me a query'
        ]
        question_lower = question.lower().strip()
        return any(keyword in question_lower for keyword in sql_keywords)
    
    def process_question(self, question: str, show_reasoning: bool = True) -> Dict[str, Any]:
        """
        Process a natural language question and return response.
        Only generates SQL if explicitly asked in the question.
        
        Args:
            question: Natural language question
            show_reasoning: Whether to display reasoning trace
            
        Returns:
            Dictionary with results and metadata
        """
        reasoning = ReasoningTrace()
        
        # Check if user is asking for SQL
        is_sql_request = self._is_sql_request(question)
        
        # Step 1: Analyze question
        reasoning.add_step(
            "Analyzing question",
            f"User asked: '{question}'" + (f" [SQL requested]" if is_sql_request else ""),
            "📋"
        )
        
        # Build the prompt with context about SQL request
        system_context = self.system_prompt
        if not is_sql_request:
            system_context += "\n\nIMPORTANT: The user is NOT asking for SQL code. Just answer their question directly without generating SQL queries."
        
        # Send question to agent
        try:
            response = self.chat.send_message(
                f"{system_context}\n\nUser question: {question}"
            )
        except Exception as e:
            if show_reasoning:
                reasoning.display()
            display_error(f"Failed to get response from LLM: {str(e)}")
            return {"success": False, "error": str(e)}
        
        # Process function calls iteratively
        max_iterations = 10
        iteration = 0
        last_result = None
        
        while iteration < max_iterations:
            iteration += 1
            
            # Check if response has function calls
            if not response.candidates[0].content.parts:
                break
            
            part = response.candidates[0].content.parts[0]
            
            # Check if it's a function call
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                tool_name = function_call.name
                tool_args = dict(function_call.args)
                
                # Display tool call
                reasoning.add_step(
                    f"Calling tool: {tool_name}",
                    f"Arguments: {json.dumps(tool_args, indent=2)}",
                    "🔧"
                )
                
                if show_reasoning:
                    display_tool_call(tool_name, tool_args)
                
                # Execute tool
                tool_result = self._execute_tool(tool_name, tool_args)
                last_result = tool_result
                
                # For execute_sql, check if we need to retry
                if tool_name == "execute_sql" and not tool_result.get("success"):
                    reasoning.add_step(
                        "Query failed, analyzing error",
                        f"Error: {tool_result.get('error')}",
                        "⚠️"
                    )
                
                # Send result back to agent
                try:
                    response = self.chat.send_message(
                        genai.protos.Content(
                            parts=[
                                genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=tool_name,
                                        response={"result": tool_result}
                                    )
                                )
                            ]
                        )
                    )
                except Exception as e:
                    if show_reasoning:
                        reasoning.display()
                    display_error(f"Error processing tool result: {str(e)}")
                    return {"success": False, "error": str(e)}
            
            # Check if response has text (final answer)
            elif hasattr(part, 'text') and part.text:
                reasoning.add_step(
                    "Generating response",
                    "Creating human-readable summary",
                    "💬"
                )
                
                # Display reasoning trace
                if show_reasoning:
                    reasoning.display()
                
                # Display results if we executed SQL
                if last_result and isinstance(last_result, dict) and "sql" in last_result:
                    display_query_results(last_result, show_sql=True)
                
                # Display summary
                if show_reasoning:
                    display_summary(part.text)
                
                # Extract SQL from response text if SQL was requested
                sql = ""
                rows = []
                columns = []
                
                # First, check if we have SQL from executed query
                if last_result and isinstance(last_result, dict):
                    sql = last_result.get("sql", "")
                    rows = last_result.get("results", [])
                    columns = last_result.get("columns", [])
                
                # If SQL request but no SQL from execution, try to extract from response text
                if is_sql_request and not sql and part.text:
                    # Extract SQL from the response - look for SELECT statement
                    text_lower = part.text.lower()
                    if 'select' in text_lower or 'sql' in text_lower:
                        # Try to find SQL in the response
                        sql_pattern = r'(?:```sql\s*(.*?)\s*```|(?:^|\n)(SELECT\s+.*?)(?:\n|$))'
                        matches = re.findall(sql_pattern, part.text, re.IGNORECASE | re.DOTALL)
                        if matches:
                            # Get the longest match which is likely the SQL
                            sql = max(matches, key=lambda x: len(x) if isinstance(x, str) else 0) if isinstance(matches[0], tuple) else matches[0]
                            if isinstance(sql, tuple):
                                sql = next((s for s in sql if s), "")
                            sql = sql.strip() if sql else ""
                
                # Create reasoning steps in the format expected by frontend
                # Take first 2 steps as key reasoning points
                reasoning_steps = reasoning.steps[:2] if reasoning.steps else []
                
                return {
                    "success": True,
                    "question": question,
                    "summary": part.text,
                    "reasoning": reasoning_steps,
                    "sql": sql,
                    "result": {
                        "columns": columns,
                        "rows": rows
                    },
                    "status": "success" if rows else ("empty" if sql else "success"),
                    "isExpensive": False,
                    "databaseAvailable": self.database_available,
                    "isSqlRequest": is_sql_request
                }
            else:
                break
        
        # If we got here, something went wrong
        if show_reasoning:
            reasoning.display()
        
        # Format error response
        sql = ""
        rows = []
        columns = []
        summary = ""
        
        if last_result and isinstance(last_result, dict):
            sql = last_result.get("sql", "")
            rows = last_result.get("results", [])
            columns = last_result.get("columns", [])
            summary = f"Query executed with {len(rows)} results"
        
        if not summary:
            summary = "Agent could not complete the task fully"
        
        reasoning_steps = reasoning.steps[:2] if reasoning.steps else []
        
        return {
            "success": False,
            "question": question,
            "summary": summary,
            "reasoning": reasoning_steps,
            "sql": sql,
            "result": {
                "columns": columns,
                "rows": rows
            },
            "status": "error",
            "error": "Agent did not complete the task",
            "databaseAvailable": self.database_available,
            "isSqlRequest": is_sql_request
        }
    
    def reset_chat(self):
        """Reset the chat session."""
        self.chat = self.model.start_chat(enable_automatic_function_calling=False)
    
    def close(self):
        """Clean up resources."""
        self.db_tools.close()

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
        
        # Store database path
        self.db_path = db_path
        
        # Initialize database tools
        self.db_tools = DatabaseTools(db_path)
        self.database_available = self.db_tools.available
        
        # System prompt for the agent - adjust based on database availability
        if self.database_available:
            self.system_prompt = """You are an expert SQL assistant that helps users query databases using natural language.

IMPORTANT - ALWAYS EXECUTE QUERIES:

**For SQL/Data Requests:**
1. Use get_schema_info() to understand database structure
2. Generate the appropriate SQL query
3. ALWAYS call execute_sql() to run the query and get results
4. Return both the SQL and the actual data results

**For General Questions:**
- Answer directly without SQL
- Keep it concise (2-3 sentences)

CRITICAL: When users ask for data, you MUST execute the SQL query and return actual results. Never just generate SQL without executing it.

Your workflow for data queries:
Step 1: get_schema_info() → understand tables/columns
Step 2: Generate SQL query
Step 3: execute_sql(query) → get actual data
Step 4: Return results with the query

Always execute queries to provide complete answers."""
        else:
            self.system_prompt = """You are an expert SQL assistant. No database is connected, so you can only generate SQL queries.

**When user asks for SQL or data queries:**
- Generate complete, executable SQL queries
- Use standard table names (users, customers, orders, products, employees)
- Use common columns (id, name, email, date, amount, status)
- Include LIMIT clauses for safety
- State your assumptions clearly
- Note that the query cannot be executed without a database

**When user asks general questions:**
- Answer directly without SQL
- Be concise and clear

Provide helpful SQL queries with clear assumptions about table structure."""
        
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
        """Check if the question is asking for data query or SQL generation."""
        sql_keywords = [
            'show', 'list', 'get', 'find', 'fetch', 'retrieve', 'display',
            'what are', 'how many', 'count', 'total', 'sum', 'average',
            'top', 'bottom', 'first', 'last', 'all', 'sql', 'query',
            'write query', 'create query', 'generate sql', 'select'
        ]
        # Questions that are NOT SQL requests
        non_sql_keywords = [
            'what is', 'explain', 'how does', 'why', 'difference between',
            'definition', 'meaning', 'purpose', 'concept'
        ]
        question_lower = question.lower().strip()
        
        # Check if it's explicitly not an SQL request
        if any(keyword in question_lower for keyword in non_sql_keywords):
            return False
        
        # Check if it's an SQL request
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
                            
                            # If we extracted SQL and database is available, execute it
                            if sql and self.database_available:
                                try:
                                    exec_result = self._execute_tool("execute_sql", {"sql": sql})
                                    if exec_result.get("success"):
                                        rows = exec_result.get("results", [])
                                        columns = exec_result.get("columns", [])
                                        reasoning.add_step(
                                            "Query executed",
                                            f"Found {len(rows)} result(s)",
                                            "✓"
                                        )
                                except Exception as e:
                                    # If execution fails, still return the SQL
                                    reasoning.add_step(
                                        "Execution note",
                                        f"SQL generated but execution had issues: {str(e)}",
                                        "⚠️"
                                    )
                
                # Format response based on request type
                if is_sql_request and sql:
                    return {
                        "success": True,
                        "question": question,
                        "summary": "",
                        "reasoning": [],  # No reasoning for SQL queries
                        "sql": sql,
                        "result": {
                            "columns": columns,
                            "rows": rows
                        },
                        "status": "success" if rows else "empty",
                        "databaseAvailable": self.database_available,
                        "isSqlRequest": True
                    }
                else:
                    # General question - show answer in 2-point reasoning format
                    answer_lines = part.text.strip().split('\n')
                    # Extract key points (max 2)
                    key_points = []
                    for line in answer_lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key_points.append({
                                "step": f"Point {len(key_points) + 1}",
                                "detail": line,
                                "icon": "💡"
                            })
                            if len(key_points) >= 2:
                                break
                    
                    # If we didn't get 2 points, create them from summary
                    if len(key_points) < 2:
                        sentences = part.text.replace('\n', ' ').split('. ')
                        key_points = [
                            {"step": "Point 1", "detail": sentences[0] + '.', "icon": "💡"},
                            {"step": "Point 2", "detail": sentences[1] + '.' if len(sentences) > 1 else "Additional context provided above.", "icon": "💡"}
                        ]
                    
                    return {
                        "success": True,
                        "question": question,
                        "summary": part.text,
                        "reasoning": key_points[:2],  # Exactly 2 points
                        "sql": "",
                        "result": {
                            "columns": [],
                            "rows": []
                        },
                        "status": "success",
                        "databaseAvailable": self.database_available,
                        "isSqlRequest": False
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

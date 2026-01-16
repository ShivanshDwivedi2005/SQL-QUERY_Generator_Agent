"""
Agent orchestrator with Gemini function calling and self-correction.
"""
import os
import json
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
        
        # System prompt for the agent
        self.system_prompt = """You are an expert SQL assistant that helps users query databases using natural language.

Your approach:
1. **Understand the question**: Analyze what the user is asking for
2. **Explore schema**: Use get_schema_info to understand available tables and their structure
3. **Explore data** (if needed): Use explore_data to see sample values and understand the data
4. **Generate SQL**: Create a correct, efficient SQL query
5. **Execute**: Use execute_sql to run the query
6. **Interpret**: Provide a human-readable summary of the results

**Important guidelines:**
- ALWAYS explore the schema before generating SQL (unless it's a meta-query about tables)
- For complex questions, explore the data to understand relationships and values
- Generate clean, efficient SQL with proper JOINs and WHERE clauses
- Handle ambiguous terms by making reasonable assumptions and stating them
- If a query fails, analyze the error and try a different approach
- For "recent" or "top" queries, make explicit assumptions (e.g., "assuming recent = last 30 days")
- Be precise with table and column names
- Add appropriate LIMIT clauses for large result sets

**For meta-queries:**
- "What tables exist?" → Use get_schema_info() with no table_name
- "Show schema of X" → Use get_schema_info(table_name="X")
- "Which table has most rows?" → Use get_table_stats()

Think step by step and explain your reasoning clearly."""
        
        # Define tools for function calling
        self.tools = self._define_tools()
        
        # Initialize model with function calling
        self.model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=genai.types.GenerationConfig(
                temperature=TEMPERATURE,
            ),
            tools=self.tools
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
    
    def process_question(self, question: str, show_reasoning: bool = True) -> Dict[str, Any]:
        """
        Process a natural language question and return SQL results.
        
        Args:
            question: Natural language question
            show_reasoning: Whether to display reasoning trace
            
        Returns:
            Dictionary with results and metadata
        """
        reasoning = ReasoningTrace()
        
        # Step 1: Analyze question
        reasoning.add_step(
            "Analyzing question",
            f"User asked: '{question}'",
            "📋"
        )
        
        # Send question to agent
        try:
            response = self.chat.send_message(
                f"{self.system_prompt}\n\nUser question: {question}"
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
                
                return {
                    "success": True,
                    "question": question,
                    "summary": part.text,
                    "last_result": last_result,
                    "reasoning_steps": reasoning.steps
                }
            else:
                break
        
        # If we got here, something went wrong
        if show_reasoning:
            reasoning.display()
        
        if last_result:
            return {
                "success": True,
                "question": question,
                "last_result": last_result,
                "reasoning_steps": reasoning.steps
            }
        
        return {
            "success": False,
            "error": "Agent did not complete the task",
            "reasoning_steps": reasoning.steps
        }
    
    def reset_chat(self):
        """Reset the chat session."""
        self.chat = self.model.start_chat(enable_automatic_function_calling=False)
    
    def close(self):
        """Clean up resources."""
        self.db_tools.close()

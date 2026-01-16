"""
Display utilities for beautiful terminal output using Rich.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich import box
from typing import List, Dict, Any

console = Console()


class ReasoningTrace:
    """Collect and display reasoning steps."""
    
    def __init__(self):
        self.steps = []
        self.current_step = 0
    
    def add_step(self, title: str, content: str, icon: str = "→"):
        """Add a reasoning step."""
        self.current_step += 1
        self.steps.append({
            "step": self.current_step,
            "title": title,
            "content": content,
            "icon": icon
        })
    
    def display(self):
        """Display all reasoning steps."""
        console.print("\n[bold cyan]🤔 REASONING TRACE[/bold cyan]")
        console.print("━" * 80, style="cyan")
        
        for step in self.steps:
            console.print(f"\n[bold yellow][Step {step['step']}][/bold yellow] [bold white]{step['icon']} {step['title']}[/bold white]")
            console.print(f"  {step['content']}", style="dim")
    
    def clear(self):
        """Clear all steps."""
        self.steps = []
        self.current_step = 0


def display_query_results(result: Dict[str, Any], show_sql: bool = True):
    """
    Display SQL query results in a formatted table.
    
    Args:
        result: Result dictionary from execute_sql
        show_sql: Whether to show the SQL query
    """
    if not result["success"]:
        # Display error
        console.print("\n[bold red]❌ QUERY FAILED[/bold red]")
        console.print("━" * 80, style="red")
        console.print(f"[red]Error: {result['error']}[/red]")
        console.print(f"[dim]Type: {result.get('error_type', 'Unknown')}[/dim]")
        if show_sql:
            console.print(f"\n[dim]SQL:[/dim]")
            sql_syntax = Syntax(result['sql'], "sql", theme="monokai", line_numbers=False)
            console.print(sql_syntax)
        return
    
    # Display SQL if requested
    if show_sql:
        console.print("\n[bold green]📊 SQL QUERY[/bold green]")
        console.print("━" * 80, style="green")
        sql_syntax = Syntax(result['sql'], "sql", theme="monokai", line_numbers=False)
        console.print(sql_syntax)
    
    # Display results
    console.print("\n[bold green]✓ RESULTS[/bold green]")
    console.print("━" * 80, style="green")
    
    if result["row_count"] == 0:
        console.print("[yellow]No rows returned.[/yellow]")
    else:
        # Create table
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        
        # Add columns
        for col in result["columns"]:
            table.add_column(col, style="cyan")
        
        # Add rows (limit display to 50 rows)
        display_limit = min(50, len(result["results"]))
        for row in result["results"][:display_limit]:
            table.add_row(*[str(row[col]) for col in result["columns"]])
        
        console.print(table)
        
        if len(result["results"]) > display_limit:
            console.print(f"\n[dim]... and {len(result['results']) - display_limit} more rows[/dim]")
    
    # Display metadata
    console.print(f"\n[dim]Rows: {result['row_count']} | Time: {result['execution_time']}s[/dim]")


def display_summary(summary: str):
    """Display natural language summary."""
    console.print("\n[bold blue]💬 SUMMARY[/bold blue]")
    console.print("━" * 80, style="blue")
    console.print(summary)


def display_welcome():
    """Display welcome message."""
    welcome_text = """
# 🚀 Natural Language to SQL System

Ask questions in plain English, and I'll generate SQL queries with reasoning!

**Features:**
- 🧠 Intelligent schema exploration
- 🔄 Self-correction on errors
- 🛡️ Safe, read-only queries
- 📊 Beautiful result displays

**Examples:**
- "How many customers are from Brazil?"
- "Which 5 artists have the most tracks?"
- "Show me the schema of the Invoice table"

Type 'exit' or 'quit' to stop.
    """
    console.print(Panel(Markdown(welcome_text), border_style="green", padding=(1, 2)))


def display_error(message: str):
    """Display error message."""
    console.print(f"\n[bold red]❌ Error:[/bold red] {message}")


def display_thinking():
    """Display thinking indicator."""
    console.print("\n[dim]🤔 Thinking...[/dim]")


def display_tool_call(tool_name: str, args: Dict[str, Any]):
    """Display tool being called."""
    args_str = ", ".join([f"{k}={v}" for k, v in args.items() if v is not None])
    console.print(f"[dim]🔧 Calling: {tool_name}({args_str})[/dim]")


def display_schema_info(schema: Dict[str, Any]):
    """Display schema information in a readable format."""
    if schema.get("type") == "all_tables":
        console.print("\n[bold cyan]📚 Available Tables[/bold cyan]")
        console.print("━" * 80, style="cyan")
        for table in schema["tables"]:
            console.print(f"  • {table}")
        console.print(f"\n[dim]Total: {schema['count']} tables[/dim]")
    
    elif schema.get("type") == "table_schema":
        console.print(f"\n[bold cyan]📋 Schema: {schema['table_name']}[/bold cyan]")
        console.print("━" * 80, style="cyan")
        
        # Columns table
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Column", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Nullable", style="yellow")
        table.add_column("Primary Key", style="red")
        
        for col in schema["columns"]:
            table.add_row(
                col["name"],
                col["type"],
                "Yes" if col["nullable"] else "No",
                "✓" if col["primary_key"] else ""
            )
        
        console.print(table)
        
        # Foreign keys
        if schema["foreign_keys"]:
            console.print("\n[bold cyan]🔗 Foreign Keys[/bold cyan]")
            for fk in schema["foreign_keys"]:
                console.print(f"  • {fk['column']} → {fk['references_table']}.{fk['references_column']}")

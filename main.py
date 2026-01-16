"""
Main CLI interface for the Natural Language to SQL system.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST before importing config
load_dotenv()

from src.agent import SQLAgent
from src.display import display_welcome, display_error, display_thinking, console
from config import DATABASE_PATH


def run_interactive_mode():
    """Run the system in interactive CLI mode."""
    display_welcome()
    
    # Check if database exists
    if not DATABASE_PATH.exists():
        display_error(f"Database not found at {DATABASE_PATH}")
        console.print("\n[yellow]Please download the Chinook database:[/yellow]")
        console.print("1. Visit: https://github.com/lerocha/chinook-database")
        console.print("2. Download chinook.db (SQLite version)")
        console.print(f"3. Place it in: {DATABASE_PATH}")
        return
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        display_error("GEMINI_API_KEY not found in environment")
        console.print("\n[yellow]To get your API key:[/yellow]")
        console.print("1. Visit: https://aistudio.google.com/app/apikey")
        console.print("2. Create a new API key")
        console.print("3. Create a .env file with: GEMINI_API_KEY=your_key_here")
        return
    
    # Initialize agent
    try:
        agent = SQLAgent()
        console.print("[green]✓ Agent initialized successfully![/green]\n")
    except Exception as e:
        display_error(f"Failed to initialize agent: {str(e)}")
        return
    
    # Main loop
    try:
        while True:
            # Get user input
            console.print("\n" + "─" * 80)
            question = console.input("\n[bold cyan]Ask a question:[/bold cyan] ").strip()
            
            if not question:
                continue
            
            # Check for exit commands
            if question.lower() in ["exit", "quit", "q"]:
                console.print("\n[yellow]Goodbye! 👋[/yellow]")
                break
            
            # Special command to reset conversation
            if question.lower() == "reset":
                agent.reset_chat()
                console.print("[green]✓ Conversation reset[/green]")
                continue
            
            # Process question
            display_thinking()
            try:
                result = agent.process_question(question, show_reasoning=True)
                
                if not result.get("success"):
                    display_error(result.get("error", "Unknown error"))
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                continue
            except Exception as e:
                display_error(f"Unexpected error: {str(e)}")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Goodbye! 👋[/yellow]")
    finally:
        agent.close()


def run_demo_queries():
    """Run a set of demo queries to showcase the system."""
    console.print("[bold green]🎬 Running Demo Queries[/bold green]\n")
    
    # Check database
    if not DATABASE_PATH.exists():
        display_error(f"Database not found at {DATABASE_PATH}")
        return
    
    # Initialize agent
    try:
        agent = SQLAgent()
    except Exception as e:
        display_error(f"Failed to initialize agent: {str(e)}")
        return
    
    # Demo queries organized by complexity
    demo_queries = {
        "Simple Queries": [
            "How many customers are from Brazil?",
            "List all albums by AC/DC",
            "What tables exist in this database?",
        ],
        "Moderate Queries": [
            "Which 5 artists have the most tracks?",
            "Show me the schema of the Invoice table",
            "Total revenue by country, sorted highest first",
        ],
        "Complex Multi-step Queries": [
            "Which customers have never made a purchase?",
            "Which artist has tracks in the most playlists?",
            "Are there any genres with no sales?",
        ],
        "Edge Cases": [
            "Show me recent orders",  # Ambiguous
            "Which table has the most rows?",  # Meta-query
        ]
    }
    
    try:
        for category, queries in demo_queries.items():
            console.print(f"\n[bold magenta]{'=' * 80}[/bold magenta]")
            console.print(f"[bold magenta]{category}[/bold magenta]")
            console.print(f"[bold magenta]{'=' * 80}[/bold magenta]\n")
            
            for i, query in enumerate(queries, 1):
                console.print(f"\n[bold yellow]Query {i}/{len(queries)}:[/bold yellow] [white]{query}[/white]")
                console.print("─" * 80)
                
                try:
                    result = agent.process_question(query, show_reasoning=True)
                    
                    if not result.get("success"):
                        display_error(result.get("error", "Unknown error"))
                    
                    # Wait for user to continue
                    if i < len(queries):
                        console.input("\n[dim]Press Enter to continue...[/dim]")
                    
                    # Reset chat for each query to avoid context leakage
                    agent.reset_chat()
                
                except Exception as e:
                    display_error(f"Error processing query: {str(e)}")
                    continue
        
        console.print("\n[bold green]✓ Demo completed![/bold green]")
    
    finally:
        agent.close()


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo_queries()
    else:
        run_interactive_mode()


if __name__ == "__main__":
    main()

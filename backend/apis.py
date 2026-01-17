from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

from src.agent import SQLAgent
from config import DATABASE_PATH

app = FastAPI(title="AI SQL Agent API", version="1.0.0")

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store uploaded databases
UPLOADED_DB_DIR = Path(__file__).parent / "uploaded_dbs"
UPLOADED_DB_DIR.mkdir(exist_ok=True)

class QuestionRequest(BaseModel):
    question: str
    show_reasoning: bool = True

class DatabaseInfo(BaseModel):
    databases: list[str]
    current: str | None

# Global variable to track current database
app.state.current_db = None
app.state.agent = None

@app.on_event("startup")
async def startup():
    """Initialize agent on startup."""
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠ WARNING: GEMINI_API_KEY not set. Set it in .env file.")
        print("  Get your key from: https://aistudio.google.com/app/apikey")
        # Don't raise error, allow server to start
    
    # Use default database path if none specified
    db_path = app.state.current_db if hasattr(app.state, 'current_db') and app.state.current_db else str(DATABASE_PATH)
    
    try:
        # Initialize agent
        app.state.agent = SQLAgent(db_path=db_path)
        
        # Log database status
        if app.state.agent.database_available:
            print(f"✓ Database available: {db_path}")
        else:
            print(f"⚠ Database not found: {db_path}")
            print("  Running in fallback mode (API-based SQL generation)")
    except Exception as e:
        print(f"⚠ Error initializing agent: {e}")
        # Create a basic agent anyway
        app.state.agent = None

@app.on_event("shutdown")
async def shutdown():
    """Close agent on shutdown."""
    if hasattr(app.state, 'agent') and app.state.agent:
        app.state.agent.close()

@app.get("/databases", response_model=DatabaseInfo)
def list_databases():
    """List available databases and current selection."""
    # Get uploaded databases
    uploaded_dbs = []
    if UPLOADED_DB_DIR.exists():
        uploaded_dbs = [f.stem for f in UPLOADED_DB_DIR.glob("*.db") if f.name != ".gitkeep"]
    
    # Include default database if it exists
    default_name = "default"
    if Path(DATABASE_PATH).exists():
        uploaded_dbs.insert(0, default_name)
    
    # Determine current database
    current = None
    if hasattr(app.state, 'current_db') and app.state.current_db:
        current_path = Path(app.state.current_db)
        if current_path == DATABASE_PATH:
            current = default_name
        else:
            current = current_path.stem
    elif Path(DATABASE_PATH).exists():
        current = default_name
    
    return {
        "databases": uploaded_dbs,
        "current": current
    }

@app.post("/databases/{db_name}/select")
def select_database(db_name: str):
    """Select a database to use."""
    if db_name == "default":
        db_path = str(DATABASE_PATH)
    else:
        db_path = str(UPLOADED_DB_DIR / f"{db_name}.db")
    
    if not Path(db_path).exists():
        raise HTTPException(status_code=404, detail=f"Database '{db_name}' not found")
    
    # Reinitialize agent with new database
    app.state.current_db = db_path
    app.state.agent.close()
    app.state.agent = SQLAgent(db_path=db_path)
    
    return {
        "success": True,
        "message": f"Switched to database: {db_name}",
        "database": db_name
    }

@app.post("/upload-database")
async def upload_database(file: UploadFile = File(...)):
    """Upload a SQLite database."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file.filename.endswith('.db'):
        raise HTTPException(status_code=400, detail="Only .db files are allowed")
    
    try:
        # Save the file to uploaded_dbs directory
        db_path = UPLOADED_DB_DIR / file.filename
        
        # Read and save file content
        content = await file.read()
        with open(db_path, "wb") as buffer:
            buffer.write(content)
        
        # Verify it's a valid SQLite database
        import sqlite3
        try:
            conn = sqlite3.connect(str(db_path), check_same_thread=False)
            conn.execute("SELECT 1")
            conn.close()
        except sqlite3.DatabaseError:
            # Clean up invalid file
            db_path.unlink()
            raise HTTPException(status_code=400, detail="Invalid SQLite database file")
        
        # Automatically select the uploaded database
        if hasattr(app.state, 'agent') and app.state.agent:
            app.state.agent.close()
        
        app.state.current_db = str(db_path)
        app.state.agent = SQLAgent(db_path=str(db_path))
        
        db_name = file.filename[:-3]  # Remove .db extension
        
        print(f"✓ Database '{db_name}' uploaded and selected successfully")
        
        return {
            "success": True,
            "message": f"Database '{db_name}' uploaded and activated",
            "database": db_name
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload database: {str(e)}")

@app.post("/execute-sql")
def execute_raw_sql(req: QuestionRequest):
    """Execute raw SQL query directly on the selected database."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="SQL query cannot be empty")
    
    if not hasattr(app.state, 'agent') or app.state.agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized. Please set GEMINI_API_KEY in .env file.")
    
    if not app.state.agent.database_available:
        raise HTTPException(status_code=400, detail="No database is currently selected")
    
    try:
        sql_query = req.question.strip()
        
        # Use the agent's execute_sql tool
        result = app.state.agent.db_tools.execute_sql(sql_query)
        
        if result.get("success"):
            return {
                "success": True,
                "sql": sql_query,
                "result": {
                    "columns": result.get("columns", []),
                    "rows": result.get("results", [])
                },
                "status": "success",
                "message": f"Query executed successfully. {len(result.get('results', []))} row(s) returned."
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Query execution failed"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing SQL: {str(e)}")

@app.post("/ask")
def ask_question(req: QuestionRequest):
    """Process a natural language question and return SQL results."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if not hasattr(app.state, 'agent') or app.state.agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized. Please set GEMINI_API_KEY in .env file.")

    try:
        result = app.state.agent.process_question(
            req.question.strip(),
            show_reasoning=req.show_reasoning
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/view")
def view_database():
    """Get database schema and sample data for all tables."""
    if not hasattr(app.state, 'agent') or app.state.agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    if not app.state.agent.database_available:
        raise HTTPException(status_code=404, detail="No database is currently selected")
    
    try:
        import sqlite3
        db_path = app.state.agent.db_tools.db_path
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        result = {
            "database": Path(db_path).stem,
            "tables": []
        }
        
        for table_name in tables:
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            columns = [
                {
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "default_value": col[4],
                    "pk": bool(col[5])
                }
                for col in columns_info
            ]
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Get sample data (first 5 rows)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            sample_rows = cursor.fetchall()
            column_names = [col[0] for col in cursor.description]
            
            sample_data = [
                {col: row[i] for i, col in enumerate(column_names)}
                for row in sample_rows
            ]
            
            result["tables"].append({
                "name": table_name,
                "columns": columns,
                "row_count": row_count,
                "sample_data": sample_data
            })
        
        conn.close()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to view database: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_initialized": hasattr(app.state, 'agent') and app.state.agent is not None,
        "database_available": hasattr(app.state, 'agent') and app.state.agent and app.state.agent.database_available
    }

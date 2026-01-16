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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
def startup():
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY not set")
    
    # Get the current database path
    db_path = app.state.current_db or str(DATABASE_PATH)
    
    # Initialize agent
    app.state.agent = SQLAgent(db_path=db_path)
    
    # Log database status
    if app.state.agent.database_available:
        print(f"✓ Database available: {db_path}")
    else:
        print(f"⚠ Database not found: {db_path}")
        print("  Running in fallback mode (API-based SQL generation)")

@app.on_event("shutdown")
def shutdown():
    app.state.agent.close()

@app.get("/databases", response_model=DatabaseInfo)
def list_databases():
    """List available databases and current selection."""
    # Get uploaded databases
    uploaded_dbs = []
    if UPLOADED_DB_DIR.exists():
        uploaded_dbs = [f.stem for f in UPLOADED_DB_DIR.glob("*.db")]
    
    # Include default database if it exists
    default_name = "default"
    if Path(DATABASE_PATH).exists():
        uploaded_dbs.insert(0, default_name)
    
    current = app.state.current_db
    if current is None and Path(DATABASE_PATH).exists():
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
    if not file.filename.endswith('.db'):
        raise HTTPException(status_code=400, detail="Only .db files are allowed")
    
    try:
        # Save the file
        db_path = UPLOADED_DB_DIR / file.filename
        with open(db_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Automatically select the uploaded database
        app.state.current_db = str(db_path)
        app.state.agent.close()
        app.state.agent = SQLAgent(db_path=str(db_path))
        
        db_name = file.filename[:-3]  # Remove .db extension
        return {
            "success": True,
            "message": f"Database '{db_name}' uploaded successfully",
            "database": db_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload database: {str(e)}")

@app.post("/ask")
def ask_question(req: QuestionRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        result = app.state.agent.process_question(
            req.question.strip(),
            show_reasoning=req.show_reasoning
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

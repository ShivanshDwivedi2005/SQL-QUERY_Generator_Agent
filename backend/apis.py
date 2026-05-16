from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv(override=True)

from config import DATABASE_NAME, DATABASE_URL, MAX_UPLOAD_SIZE_BYTES
from src.agent import SQLAgent

app = FastAPI(title="AI SQL Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    show_reasoning: bool = True


class DatabaseInfo(BaseModel):
    databases: list[str]
    current: str | None
    provider: str = "neon"
    connected: bool = False


app.state.agent = None


def _sync_database_status() -> tuple[bool, str | None, str | None]:
    """Refresh connection state and return (connected, database_name, connection_error)."""
    agent = getattr(app.state, "agent", None)
    if not agent:
        return False, None, None

    if DATABASE_URL:
        agent.db_tools.ensure_connected()
        agent.database_available = agent.db_tools.available

    connected = bool(agent.database_available)
    database_name = agent.db_tools.database_name if connected else DATABASE_NAME
    connection_error = None if connected else agent.db_tools.connection_error
    return connected, database_name, connection_error


@app.on_event("startup")
async def startup():
    """Initialize the agent and Neon/PostgreSQL connection."""
    if not os.getenv("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY not set. Set it in .env file.")
        print("Get your key from: https://aistudio.google.com/app/apikey")

    if not DATABASE_URL:
        print("WARNING: DATABASE_URL/NEON_DATABASE_URL not set.")
        print("The app will run in SQL-generation-only mode until Neon is configured.")

    try:
        app.state.agent = SQLAgent(db_path=DATABASE_URL)
        if app.state.agent.database_available:
            print(f"Database available: {app.state.agent.db_tools.database_name}")
        else:
            print("Database not connected. Running in fallback SQL-generation mode.")
            if app.state.agent.db_tools.connection_error:
                print(f"Database connection error: {app.state.agent.db_tools.connection_error}")
    except Exception as e:
        print(f"Error initializing agent: {e}")
        app.state.agent = None


@app.on_event("shutdown")
async def shutdown():
    """Close agent on shutdown."""
    if hasattr(app.state, "agent") and app.state.agent:
        app.state.agent.close()


@app.get("/databases", response_model=DatabaseInfo)
def list_databases():
    """Return the configured Neon/PostgreSQL database."""
    connected, database_name, _ = _sync_database_status()

    return {
        "databases": [database_name] if DATABASE_URL else [],
        "current": database_name if connected else None,
        "provider": "neon",
        "connected": connected,
    }


@app.post("/databases/{db_name}/select")
def select_database(db_name: str):
    """Neon uses the configured DATABASE_URL, so runtime DB switching is disabled."""
    raise HTTPException(
        status_code=400,
        detail="Database switching is disabled. Set DATABASE_URL/NEON_DATABASE_URL to choose the Neon database.",
    )


@app.post("/upload-database")
async def upload_database():
    """SQLite file upload is no longer supported after moving to Neon PostgreSQL."""
    raise HTTPException(
        status_code=410,
        detail="SQLite uploads are no longer supported. Configure a Neon PostgreSQL DATABASE_URL instead.",
    )


@app.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):
    """Upload a CSV file and import it as a new Neon/PostgreSQL table."""
    if not hasattr(app.state, "agent") or app.state.agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    connected, _, connection_error = _sync_database_status()
    if not connected:
        detail = "No Neon PostgreSQL database is currently connected"
        if connection_error:
            detail = f"{detail}: {connection_error}"
        raise HTTPException(status_code=400, detail=detail)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Data size is larger than 5 MB")

    result = app.state.agent.db_tools.upload_csv_data(file.filename, content)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to upload data"))

    return result


@app.post("/execute-sql")
def execute_raw_sql(req: QuestionRequest):
    """Validate and execute raw read-only SQL on Neon/PostgreSQL."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="SQL query cannot be empty")

    if not hasattr(app.state, "agent") or app.state.agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized. Please set GEMINI_API_KEY in .env file.")

    if not app.state.agent.database_available:
        raise HTTPException(status_code=400, detail="No Neon PostgreSQL database is currently connected")

    try:
        sql_query = req.question.strip()
        is_valid, message, modified_sql = app.state.agent.db_tools.validate_sql(sql_query)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        sql_to_execute = modified_sql or sql_query
        result = app.state.agent.db_tools.execute_sql(sql_to_execute)

        if result.get("success"):
            return {
                "success": True,
                "sql": sql_to_execute,
                "result": {
                    "columns": result.get("columns", []),
                    "rows": result.get("results", []),
                },
                "status": "success",
                "message": f"Query executed successfully. {len(result.get('results', []))} row(s) returned.",
                "validation_message": message,
            }

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

    if not hasattr(app.state, "agent") or app.state.agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized. Please set GEMINI_API_KEY in .env file.")

    try:
        return app.state.agent.process_question(
            req.question.strip(),
            show_reasoning=req.show_reasoning,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/database/view")
def view_database():
    """Get PostgreSQL schema and sample data for all user tables."""
    if not hasattr(app.state, "agent") or app.state.agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    if not app.state.agent.database_available:
        raise HTTPException(status_code=404, detail="No Neon PostgreSQL database is currently connected")

    result = app.state.agent.db_tools.get_database_view()
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.get("/health")
def health_check():
    """Health check endpoint."""
    agent = getattr(app.state, "agent", None)
    connected, database_name, connection_error = _sync_database_status()
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "database_available": connected,
        "database_name": database_name,
        "database_provider": "neon",
        "connection_error": connection_error,
    }

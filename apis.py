from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
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

class QuestionRequest(BaseModel):
    question: str
    show_reasoning: bool = True

@app.on_event("startup")
def startup():
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY not set")
    app.state.agent = SQLAgent()

@app.on_event("shutdown")
def shutdown():
    app.state.agent.close()

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

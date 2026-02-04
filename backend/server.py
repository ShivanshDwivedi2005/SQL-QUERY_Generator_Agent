from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.agent import SQLAgent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = SQLAgent()

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/query")
def query(data: dict):
    return agent.process_question(data.get("question", ""))

from fastapi import FastAPI
from src.agent.core_agent import run_agent

app = FastAPI()


@app.get("/")
def home():
    return {"message": "ER Triage Agent is running"}


@app.post("/triage")
def triage(patient: dict):
    result = run_agent(patient)
    return result
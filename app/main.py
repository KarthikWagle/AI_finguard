import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from app.agents import app_graph

load_dotenv()  # Load .env variables

app = FastAPI(title="FinGuard AI", version="0.1.0")

# Allow Streamlit (running on default port 8501) to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] ,  # In production restrict origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InvestigationRequest(BaseModel):
    alert_id: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/investigate")
def run_investigation(req: InvestigationRequest):
    # Start graph with alert_id in state
    try:
        final_state = app_graph.invoke({"alert_id": req.alert_id})
        # The report is under final_state["report"]
        return final_state.get("report", {"error": "Report missing"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

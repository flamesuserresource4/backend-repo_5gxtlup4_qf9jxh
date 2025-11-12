from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import os

from database import create_document, get_documents, get_db, DATABASE_URL, DATABASE_NAME
from schemas import Lead

app = FastAPI(title="Running With Strategy API", version="1.0.0")

# CORS
frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*" if frontend_url == "*" else frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> Dict[str, Any]:
    return {"message": "Running With Strategy API is live"}


@app.get("/test")
def test_connection() -> Dict[str, Any]:
    try:
        db = get_db()
        collections = db.list_collection_names()
        return {
            "backend": "ok",
            "database": "ok",
            "database_url": DATABASE_URL,
            "database_name": DATABASE_NAME,
            "connection_status": "connected",
            "collections": collections,
        }
    except Exception as e:
        return {
            "backend": "ok",
            "database": "error",
            "error": str(e),
            "database_url": DATABASE_URL,
            "database_name": DATABASE_NAME,
            "connection_status": "failed",
        }


@app.post("/leads")
def create_lead(lead: Lead):
    try:
        saved = create_document("lead", lead.model_dump())
        return {"status": "success", "lead": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leads")
def list_leads(limit: int = 50):
    try:
        docs = get_documents("lead", limit=limit)
        return {"status": "success", "leads": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

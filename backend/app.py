from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import scan
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],  # Allow all origins for UAT
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files in production
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=static_dir), name="static")

app.state.submit_query = "No query selected"
app.state.submit_count = 10

class InputItem(BaseModel):
    text: str = Field(..., min_length=1)
    count: int = Field(..., ge=0)

@app.get("/")
def read_root():
    # Serve index.html for production, API response for development
    if os.path.exists(static_dir):
        return FileResponse(os.path.join(static_dir, "index.html"))
    return {"ok": True}

@app.post("/search", response_model=List[str])
def search_endpoint(body: InputItem):
    try:
        query = scan.buildQuery(body.text)
        print(query)
        result = scan.search(query, scan.key, scan.id, body.count)
        return result or []
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

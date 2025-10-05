from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import scan
from pydantic import BaseModel, Field
from typing import List
from enum import Enum
import os

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("🚀 Job Search API starting up...")
    print(f"✅ Scan module loaded: {hasattr(scan, 'search')}")
    print(f"🔑 API Key configured: {'Yes' if scan.key else 'No'}")
    print(f"🔍 Search ID configured: {'Yes' if scan.id else 'No'}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "https://*.netlify.app",
        "https://*.vercel.app",
        "https://*.railway.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

class ExperienceLevel(str, Enum):
    INTERN = "intern"
    NEW_GRAD = "new grad"
    ASSOCIATE = "associate level"
    SENIOR = "senior level"
    MANAGER = "manager"

class InputItem(BaseModel):
    text: str = Field(..., min_length=1, description="Job title or position")
    level: ExperienceLevel = Field(..., description="Experience level")
    count: int = Field(..., ge=1, le=100, description="Number of job postings to retrieve")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Job Search API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/api/health")
def api_health_check():
    return {"status": "ok"}

@app.post("/search", response_model=List[str])
def search_endpoint(body: InputItem):
    try:
        # Check if API keys are configured
        if not scan.key or not scan.id:
            raise HTTPException(
                status_code=503, 
                detail="Search service not configured. Missing API keys."
            )
        
        query = scan.buildQuery(body.text, body.level)
        print(f"Query: {query}")
        print(f"Level: {body.level}")
        result = scan.search(query, scan.key, scan.id, body.count)
        return result or []
    except HTTPException:
        raise
    except Exception as e:
        print(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

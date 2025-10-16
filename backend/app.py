from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import scan
from pydantic import BaseModel, Field
from typing import List
from enum import Enum
import os
from auth_routes import router as auth_router
from saved_search_routes import router as saved_search_router
from auth_dep import get_current_user
import models  # Import models to ensure they're registered with SQLAlchemy
from scheduler import (
    start_background_scheduler, 
    stop_background_scheduler, 
    get_scheduler_status, 
    run_searches_now
)

app = FastAPI(title="Job Search API", description="API for job searching with authentication")

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

# Include authentication routes
app.include_router(auth_router)

# Include saved search routes
app.include_router(saved_search_router)

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
    return "OK"

@app.get("/health")
def health_check():
    return "OK"

@app.get("/healthz")
def healthz():
    return "OK"

@app.get("/debug/env")
def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "supabase_url_set": bool(os.environ.get("SUPABASE_URL")),
        "database_url_set": bool(os.environ.get("DATABASE_URL")),
        "jwt_secret_set": bool(os.environ.get("JWT_SECRET_KEY")),
        "supabase_key_set": bool(os.environ.get("SUPABASE_KEY"))
    }

@app.get("/debug/db")
def debug_db():
    """Debug endpoint to check database connection"""
    try:
        from db import SessionLocal, engine
        from models import SavedSearch
        
        # Test database connection
        db = SessionLocal()
        count = db.query(SavedSearch).count()
        db.close()
        
        return {
            "database_connected": True,
            "saved_searches_count": count,
            "tables_exist": True
        }
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e),
            "tables_exist": False
        }

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

@app.post("/search/protected", response_model=List[str])
def protected_search_endpoint(body: InputItem, current_user: dict = Depends(get_current_user)):
    """Protected search endpoint that requires authentication"""
    try:
        # Check if API keys are configured
        if not scan.key or not scan.id:
            raise HTTPException(
                status_code=503, 
                detail="Search service not configured. Missing API keys."
            )
        
        query = scan.buildQuery(body.text, body.level)
        print(f"Query: {query} (User: {current_user['email']})")
        print(f"Level: {body.level}")
        result = scan.search(query, scan.key, scan.id, body.count)
        return result or []
    except HTTPException:
        raise
    except Exception as e:
        print(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Scheduler management routes
@app.get("/admin/scheduler/status")
def get_scheduler_status_endpoint():
    """Get the current status of the background scheduler"""
    return get_scheduler_status()

@app.post("/admin/scheduler/start")
def start_scheduler_endpoint():
    """Start the background scheduler"""
    start_background_scheduler()
    return {"message": "Scheduler started successfully"}

@app.post("/admin/scheduler/stop")
def stop_scheduler_endpoint():
    """Stop the background scheduler"""
    stop_background_scheduler()
    return {"message": "Scheduler stopped successfully"}

@app.post("/admin/scheduler/run-now")
def run_searches_now_endpoint():
    """Manually trigger all searches immediately"""
    run_searches_now()
    return {"message": "All searches triggered successfully"}

# Startup event to start the scheduler
@app.on_event("startup")
async def startup_event():
    """Start the background scheduler when the app starts"""
    # Create database tables if they don't exist
    from db import engine, Base
    Base.metadata.create_all(bind=engine)
    
    start_background_scheduler()

# Shutdown event to stop the scheduler
@app.on_event("shutdown")
async def shutdown_event():
    """Stop the background scheduler when the app shuts down"""
    stop_background_scheduler()

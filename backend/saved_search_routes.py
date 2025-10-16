from fastapi import APIRouter, HTTPException, Depends, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import hashlib
from datetime import datetime

from auth_dep import get_current_user
from db import SessionLocal
from models import SavedSearch, SearchResult, SavedSearchCreate, SavedSearchUpdate, SavedSearchResponse
import scan

router = APIRouter(prefix="/saved-searches", tags=["saved-searches"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[SavedSearchResponse])
async def get_saved_searches(
    response: Response,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Add explicit CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    try:
        saved_searches = db.query(SavedSearch).filter(
            SavedSearch.user_id == current_user["id"]
        ).order_by(SavedSearch.created_at.desc()).all()
    except Exception as e:
        print(f"Database error in get_saved_searches: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    result = []
    for search in saved_searches:
        new_count = db.query(SearchResult).filter(
            SearchResult.saved_search_id == search.id,
            SearchResult.is_new == True
        ).count()
        
        search_dict = {
            "id": search.id,
            "name": search.name,
            "job_title": search.job_title,
            "experience_level": search.experience_level,
            "count": search.count,
            "is_active": search.is_active,
            "notification_email": search.notification_email,
            "last_run_at": search.last_run_at,
            "created_at": search.created_at,
            "new_results_count": new_count
        }
        result.append(SavedSearchResponse(**search_dict))
    
    return result

@router.post("/", response_model=SavedSearchResponse)
async def create_saved_search(
    search_data: SavedSearchCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    saved_search = SavedSearch(
        user_id=current_user["id"],
        name=search_data.name,
        job_title=search_data.job_title,
        experience_level=search_data.experience_level.value,
        count=search_data.count,
        notification_email=search_data.notification_email
    )
    
    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)
    
    search_dict = {
        "id": saved_search.id,
        "name": saved_search.name,
        "job_title": saved_search.job_title,
        "experience_level": saved_search.experience_level,
        "count": saved_search.count,
        "is_active": saved_search.is_active,
        "notification_email": saved_search.notification_email,
        "last_run_at": saved_search.last_run_at,
        "created_at": saved_search.created_at,
        "new_results_count": 0
    }
    
    return SavedSearchResponse(**search_dict)

@router.get("/{search_id}", response_model=SavedSearchResponse)
async def get_saved_search(
    search_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user["id"]
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    new_count = db.query(SearchResult).filter(
        SearchResult.saved_search_id == saved_search.id,
        SearchResult.is_new == True
    ).count()
    
    search_dict = {
        "id": saved_search.id,
        "name": saved_search.name,
        "job_title": saved_search.job_title,
        "experience_level": saved_search.experience_level,
        "count": saved_search.count,
        "is_active": saved_search.is_active,
        "notification_email": saved_search.notification_email,
        "last_run_at": saved_search.last_run_at,
        "created_at": saved_search.created_at,
        "new_results_count": new_count
    }
    
    return SavedSearchResponse(**search_dict)

@router.put("/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    search_id: int,
    search_data: SavedSearchUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user["id"]
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    

    update_data = search_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "experience_level" and value:
            setattr(saved_search, field, value.value)
        else:
            setattr(saved_search, field, value)
    
    saved_search.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(saved_search)
    
    new_count = db.query(SearchResult).filter(
        SearchResult.saved_search_id == saved_search.id,
        SearchResult.is_new == True
    ).count()
    
    search_dict = {
        "id": saved_search.id,
        "name": saved_search.name,
        "job_title": saved_search.job_title,
        "experience_level": saved_search.experience_level,
        "count": saved_search.count,
        "is_active": saved_search.is_active,
        "notification_email": saved_search.notification_email,
        "last_run_at": saved_search.last_run_at,
        "created_at": saved_search.created_at,
        "new_results_count": new_count
    }
    
    return SavedSearchResponse(**search_dict)

@router.delete("/{search_id}")
async def delete_saved_search(
    search_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user["id"]
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    db.query(SearchResult).filter(SearchResult.saved_search_id == search_id).delete()
    
    db.delete(saved_search)
    db.commit()
    
    return {"message": "Saved search deleted successfully"}

@router.post("/{search_id}/run")
async def run_saved_search(
    search_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user["id"]
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    try:
        if not scan.key or not scan.id:
            raise HTTPException(
                status_code=503, 
                detail="Search service not configured. Missing API keys."
            )
        
        print(f"Debug: job_title = '{saved_search.job_title}'")
        print(f"Debug: experience_level = '{saved_search.experience_level}' (type: {type(saved_search.experience_level)})")
        
        query = scan.buildQuery(saved_search.job_title, saved_search.experience_level)
        print(f"Debug: built query = '{query}'")
        results = scan.search(query, scan.key, scan.id, saved_search.count)
        
        if results:
            new_results_count = 0
            for result_url in results:
                result_hash = hashlib.sha256(result_url.encode()).hexdigest()
                
                existing = db.query(SearchResult).filter(
                    SearchResult.saved_search_id == search_id,
                    SearchResult.result_hash == result_hash
                ).first()
                
                if not existing:
                    new_result = SearchResult(
                        saved_search_id=search_id,
                        result_url=result_url,
                        result_hash=result_hash,
                        is_new=True
                    )
                    db.add(new_result)
                    new_results_count += 1
            
            saved_search.last_run_at = datetime.utcnow()
            db.commit()
            
            return {
                "message": "Search completed successfully",
                "total_results": len(results),
                "new_results": new_results_count
            }
        else:
            saved_search.last_run_at = datetime.utcnow()
            db.commit()
            return {
                "message": "Search completed successfully",
                "total_results": 0,
                "new_results": 0
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/{search_id}/results")
async def get_search_results(
    search_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    new_only: bool = False
):
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user["id"]
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    query = db.query(SearchResult).filter(SearchResult.saved_search_id == search_id)
    
    if new_only:
        query = query.filter(SearchResult.is_new == True)
    
    results = query.order_by(SearchResult.found_at.desc()).all()
    
    return {
        "search_name": saved_search.name,
        "total_results": len(results),
        "results": [
            {
                "id": result.id,
                "url": result.result_url,
                "found_at": result.found_at,
                "is_new": result.is_new
            }
            for result in results
        ]
    }

@router.post("/{search_id}/mark-seen")
async def mark_results_as_seen(
    search_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user["id"]
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    updated_count = db.query(SearchResult).filter(
        SearchResult.saved_search_id == search_id,
        SearchResult.is_new == True
    ).update({"is_new": False})
    
    db.commit()
    
    return {"message": f"Marked {updated_count} results as seen"}

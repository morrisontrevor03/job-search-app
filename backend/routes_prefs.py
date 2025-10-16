from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .db import SessionLocal
from .models import UserPreference
from .schemas import PrefsIn, PrefsOut
from .auth_dep import get_current_user

router = APIRouter(prefix="/preferences", tags=["preferences"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/me", response_model=PrefsOut)
def get_my_prefs(user=Depends(get_current_user), db=Depends(get_db)):
    row = db.execute(select(UserPreference).where(UserPreference.user_id == user["id"])).scalar_one_or_none()
    if not row:
        return {"data": {}, "updated_at": None}
    return {"data": row.data, "updated_at": row.updated_at.isoformat() if row.updated_at else None}

@router.put("/me", response_model=PrefsOut)
def upsert_my_prefs(payload: PrefsIn, user=Depends(get_current_user), db=Depends(get_db)):
    row = db.execute(select(UserPreference).where(UserPreference.user_id == user["id"])).scalar_one_or_none()
    if not row:
        row = UserPreference(user_id=user["id"], data=payload.data)
        db.add(row)
    else:
        row.data = payload.data
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Could not save preferences")
    db.refresh(row)
    return {"data": row.data, "updated_at": row.updated_at.isoformat() if row.updated_at else None}
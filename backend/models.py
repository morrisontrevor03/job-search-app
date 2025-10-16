import sqlalchemy as sa
from db import Base
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

# SQLAlchemy Database Models
class UserPreference(Base):
    __tablename__ = "user_preferences"
    user_id = sa.Column(sa.Uuid, primary_key=True)
    data = sa.Column(sa.JSON, nullable=False, default=dict)
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

class SavedSearch(Base):
    __tablename__ = "saved_searches"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.String, nullable=False, index=True)  # Supabase user ID
    name = sa.Column(sa.String, nullable=False)
    job_title = sa.Column(sa.String, nullable=False)
    experience_level = sa.Column(sa.String, nullable=False)
    count = sa.Column(sa.Integer, nullable=False, default=10)
    is_active = sa.Column(sa.Boolean, nullable=False, default=True)
    notification_email = sa.Column(sa.String, nullable=True)
    last_run_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

class SearchResult(Base):
    __tablename__ = "search_results"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    saved_search_id = sa.Column(sa.Integer, sa.ForeignKey("saved_searches.id"), nullable=False)
    result_url = sa.Column(sa.String, nullable=False)
    result_hash = sa.Column(sa.String, nullable=False, unique=True, index=True)
    is_new = sa.Column(sa.Boolean, nullable=False, default=True)
    found_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

# Pydantic Models for API
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

class SavedSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    job_title: str = Field(..., min_length=1, max_length=200)
    experience_level: ExperienceLevel
    count: int = Field(default=10, ge=1, le=100)
    notification_email: Optional[str] = Field(None, max_length=255)

class SavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    job_title: Optional[str] = Field(None, min_length=1, max_length=200)
    experience_level: Optional[ExperienceLevel] = None
    count: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None
    notification_email: Optional[str] = Field(None, max_length=255)

class SavedSearchResponse(BaseModel):
    id: int
    name: str
    job_title: str
    experience_level: str
    count: int
    is_active: bool
    notification_email: Optional[str]
    last_run_at: Optional[datetime]
    created_at: datetime
    new_results_count: int = 0

    class Config:
        from_attributes = True
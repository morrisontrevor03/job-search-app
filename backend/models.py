import sqlalchemy as sa
from .db import Base
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class UserPreference(Base):
    __tablename__ = "user_preferences"
    user_id = sa.Column(sa.Uuid, primary_key=True)
    data = sa.Column(sa.JSON, nullable = False, default = dict)
    updated_at = sa.Column(sa.DateTime(timezone=True, server_default=sa.func.now(), onupdate = sa.func.now()))

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
    
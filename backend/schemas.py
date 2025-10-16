from pydantic import BaseModel, Field
from typing import Any, Dict

class PrefsIn(BaseModel):
    data: Dict[str, Any] = Field(default_factor=dict)

class PrefsOut(PrefsIn):
    update_at: str | None = None
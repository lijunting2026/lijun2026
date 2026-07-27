from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SubjectCreate(BaseModel):
    name: str
    full_score: float = 100
    sort_order: int = 0

class SubjectResponse(BaseModel):
    id: str
    name: str
    full_score: float
    sort_order: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

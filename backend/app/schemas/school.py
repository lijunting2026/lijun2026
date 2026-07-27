from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class GradeCreate(BaseModel):
    name: str
    sort_order: int = 0

class GradeResponse(BaseModel):
    id: str
    name: str
    sort_order: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ClassCreate(BaseModel):
    name: str
    grade_id: str

class ClassResponse(BaseModel):
    id: str
    name: str
    grade_id: str
    grade_name: Optional[str] = None
    student_count: Optional[int] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

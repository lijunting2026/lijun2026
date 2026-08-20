from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

class ExamSubjectCreate(BaseModel):
    subject_id: str
    full_score: float
    weight: float = 1.0
    difficulty: Optional[float] = None
    discrimination: Optional[float] = None
    reliability: Optional[float] = None

class ExamCreate(BaseModel):
    name: str
    exam_date: date
    exam_type: str = "月考"
    grade_id: str
    subjects: List[ExamSubjectCreate]

class ExamSubjectResponse(BaseModel):
    id: str
    subject_id: str
    subject_name: Optional[str] = None
    full_score: float
    weight: float
    difficulty: Optional[float] = None
    discrimination: Optional[float] = None
    reliability: Optional[float] = None
    class Config:
        from_attributes = True

class ExamResponse(BaseModel):
    id: str
    name: str
    exam_date: Optional[date] = None
    exam_type: str
    grade_id: str
    grade_name: Optional[str] = None
    exam_subjects: List[ExamSubjectResponse] = []
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

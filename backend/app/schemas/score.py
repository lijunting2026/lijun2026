from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ScoreCreate(BaseModel):
    student_id: str
    exam_subject_id: str
    score_value: float
    status: str = "normal"

class ScoreBatchCreate(BaseModel):
    exam_id: str
    scores: List[ScoreCreate]

class ScoreUpdate(BaseModel):
    score_value: Optional[float] = None
    status: Optional[str] = None

class ScoreResponse(BaseModel):
    id: str
    student_id: str
    student_no: Optional[str] = None
    student_name: Optional[str] = None
    exam_subject_id: str
    subject_name: Optional[str] = None
    score_value: float
    status: str
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StudentCreate(BaseModel):
    student_no: str
    name: str
    gender: str = "未知"
    class_id: str

class StudentImport(BaseModel):
    students: List[StudentCreate]

class StudentResponse(BaseModel):
    id: str
    student_no: str
    name: str
    gender: str
    class_id: str
    class_name: Optional[str] = None
    grade_name: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class TransferRequest(BaseModel):
    target_class_id: str
    migrate_scores: bool = True

class TransferResponse(BaseModel):
    id: str
    student_no: str
    student_name: str
    original_class_name: str
    target_class_name: str
    migrated_score_count: int
    scores_follow_student: bool

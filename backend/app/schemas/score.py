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

class ScoreSummaryQuery(BaseModel):
    exam_id: Optional[str] = None
    grade_id: Optional[str] = None
    class_id: Optional[str] = None
    subject_id: Optional[str] = None

class SubjectSummary(BaseModel):
    subject_id: str
    subject_name: str
    full_score: float
    avg_score: float = 0
    max_score: float = 0
    min_score: float = 0
    median_score: float = 0
    pass_count: int = 0
    total_count: int = 0
    pass_rate: float = 0
    excellence_count: int = 0
    excellence_rate: float = 0
    fail_count: int = 0
    fail_rate: float = 0
    std_dev: float = 0

class ClassSummary(BaseModel):
    class_id: str
    class_name: str
    avg_score: float = 0
    max_score: float = 0
    min_score: float = 0
    total_count: int = 0
    rank: int = 0

class ScoreSummaryResponse(BaseModel):
    exam_name: str = ""
    grade_name: str = ""
    total_students: int = 0
    total_subjects: int = 0
    subject_summaries: list[SubjectSummary] = []
    class_summaries: list[ClassSummary] = []
    overall_avg: float = 0
    overall_pass_rate: float = 0

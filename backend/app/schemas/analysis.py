from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class SubjectStats(BaseModel):
    subject_id: str
    subject_name: str
    full_score: float
    avg_score: float
    max_score: float
    min_score: float
    pass_rate: float
    excellent_rate: float
    std_dev: float
    avg_score_rate: float

class ClassSubjectStats(BaseModel):
    class_id: str
    class_name: str
    student_count: int
    stats: List[SubjectStats]

class ExamAnalysisResponse(BaseModel):
    exam_id: str
    exam_name: str
    exam_date: Optional[str] = None
    total_students: int
    grade_stats: List[SubjectStats]
    class_stats: List[ClassSubjectStats]

class ScoreDistribution(BaseModel):
    range_label: str
    count: int
    percentage: float

class DistributionResponse(BaseModel):
    subject_id: str
    subject_name: str
    distributions: List[ScoreDistribution]

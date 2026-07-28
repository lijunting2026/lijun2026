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


class DashboardStats(BaseModel):
    grades: int
    classes: int
    subjects: int
    students: int
    exams: int
    scores: int

class RecentExamItem(BaseModel):
    exam_name: str
    exam_date: str
    avg_rate: float
    student_count: int

class SubjectStatItem(BaseModel):
    subject_name: str
    full_score: float
    avg_score: float
    max_score: float
    count: int

class TrendInfo(BaseModel):
    direction: str
    description: str

class RiskStudent(BaseModel):
    student_name: str
    student_no: str
    avg_rate: float

class SubjectAlert(BaseModel):
    subject_name: str
    avg_score: float
    level: str
    desc: str

class ClassRankItem(BaseModel):
    class_name: str
    avg_rate: float

class ClassRankGroup(BaseModel):
    grade_name: str
    classes: List[ClassRankItem]

class RegressionAlert(BaseModel):
    exam_name: str
    drop: float
    level: str
    desc: str

class DashboardResponse(BaseModel):
    regression_alerts: List[RegressionAlert]
    stats: DashboardStats
    recent_exams: List[RecentExamItem]
    subject_stats: List[SubjectStatItem]
    trend: TrendInfo
    risk_students: List[RiskStudent]
    subject_alerts: List[SubjectAlert]
    class_ranking: List[ClassRankGroup]
    exam_type_stats: dict

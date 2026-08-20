from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class BracketItem(BaseModel):
    rank_start: float
    rank_end: float
    score_start: float
    score_end: float


class ScoringSchemeCreate(BaseModel):
    name: str
    description: str = ""
    brackets: List[BracketItem]
    sort_order: float = 0


class ScoringSchemeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    brackets: Optional[List[BracketItem]] = None
    sort_order: Optional[float] = None


class ScoringSchemeResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    brackets: list = []
    is_preset: bool = False
    sort_order: float = 0
    created_at: Optional[datetime] = None

    @field_validator("id", mode="before")
    @classmethod
    def _uuid_to_str(cls, v):
        return str(v) if v is not None else v

    class Config:
        from_attributes = True


class ExamSubjectScoringConfig(BaseModel):
    exam_subject_id: str
    scoring_type: str = "raw"       # raw=原始分科目 | converted=赋分科目
    scheme_id: Optional[str] = None
    conversion_mode: str = "auto"   # auto=系统自动换算 | manual=手动赋分


class ExamScoringConfigRequest(BaseModel):
    subjects: List[ExamSubjectScoringConfig]


class ScoreLineCreate(BaseModel):
    line_name: str
    line_type: str = "total"        # total=总分线 | subject=单科线
    subject_id: Optional[str] = None
    score_value: float
    source: str = "official"        # official | reference | custom


class ScoreLineResponse(BaseModel):
    id: str
    exam_id: str
    line_name: str
    line_type: str = "total"
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    score_value: float
    source: str = "official"

    class Config:
        from_attributes = True

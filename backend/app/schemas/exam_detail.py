"""知识点库、细目表、小题分 Schema"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class KnowledgePointCreate(BaseModel):
    subject_id: str
    name: str
    parent_id: Optional[str] = None
    sort_order: int = 0
    description: str = ""


class KnowledgePointUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None
    sort_order: Optional[int] = None
    description: Optional[str] = None


class KnowledgePointResponse(BaseModel):
    id: str
    subject_id: str
    name: str
    parent_id: Optional[str] = None
    sort_order: int = 0
    description: str = ""
    children: List["KnowledgePointResponse"] = []

    class Config:
        from_attributes = True


class ExamQuestionCreate(BaseModel):
    question_no: int
    question_type: str = ""
    full_score: float
    knowledge_point_id: Optional[str] = None
    difficulty: Optional[float] = None
    cognitive_level: str = ""
    estimated_pass_rate: Optional[float] = None
    content: str = ""


class ExamQuestionResponse(BaseModel):
    id: str
    exam_subject_id: str
    question_no: int
    question_type: str
    full_score: float
    knowledge_point_id: Optional[str] = None
    knowledge_point_name: Optional[str] = None
    difficulty: Optional[float] = None
    cognitive_level: str
    estimated_pass_rate: Optional[float] = None
    content: str

    class Config:
        from_attributes = True


class ExamBlueprintImport(BaseModel):
    """命题细目表导入"""
    exam_subject_id: str
    questions: List[ExamQuestionCreate]
    difficulty: Optional[float] = None      # 试卷整体难度
    discrimination: Optional[float] = None  # 试卷整体区分度
    reliability: Optional[float] = None     # 信度


class ScoreDetailResponse(BaseModel):
    id: str
    question_id: str
    score_value: float
    question_no: Optional[int] = None
    question_type: Optional[str] = None
    full_score: Optional[float] = None
    knowledge_point_name: Optional[str] = None

    class Config:
        from_attributes = True

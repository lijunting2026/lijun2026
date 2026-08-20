"""赋分方案模型 —— 支持自定义比例区间配置"""
from sqlalchemy import Column, String, Float, Boolean, Text, JSON, ForeignKey
from sqlalchemy.types import Uuid
from app.models.base import BaseModel


class ScoringScheme(BaseModel):
    __tablename__ = "scoring_schemes"

    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    brackets = Column(JSON, nullable=False)
    is_preset = Column(Boolean, default=False)
    sort_order = Column(Float, default=0)


class ScoreLine(BaseModel):
    """考试分数线（总分线/单科线）"""
    __tablename__ = "score_lines"

    exam_id = Column(Uuid(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    line_name = Column(String(50), nullable=False)   # 本科线 / 特控线 / 专科线 / 单科线名
    line_type = Column(String(20), default="total")  # total=总分线 | subject=单科线
    subject_id = Column(Uuid(as_uuid=True), ForeignKey("subjects.id"), nullable=True)
    score_value = Column(Float, nullable=False)
    source = Column(String(20), default="official")  # official | reference | custom

"""赋分方案模型 —— 支持自定义比例区间配置"""
from sqlalchemy import Column, String, Float, Boolean, Text, JSON
from app.models.base import BaseModel


class ScoringScheme(BaseModel):
    __tablename__ = "scoring_schemes"

    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    brackets = Column(JSON, nullable=False)
    is_preset = Column(Boolean, default=False)
    sort_order = Column(Float, default=0)

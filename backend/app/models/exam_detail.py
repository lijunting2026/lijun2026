"""知识点库、细目表及小题分模型"""
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.types import Uuid
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SubjectKnowledgePoint(BaseModel):
    """知识点库 —— 按科目维护的知识点体系"""
    __tablename__ = "subject_knowledge_points"

    subject_id = Column(Uuid(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    parent_id = Column(Uuid(as_uuid=True), ForeignKey("subject_knowledge_points.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    description = Column(Text, default="")

    subject = relationship("Subject", foreign_keys=[subject_id])
    parent = relationship("SubjectKnowledgePoint", remote_side="SubjectKnowledgePoint.id", backref="children")

    __table_args__ = (
        UniqueConstraint("subject_id", "name", name="uq_knowledge_point"),
    )


class ExamQuestion(BaseModel):
    """考试小题定义 —— 对应命题细目表的逐题记录"""
    __tablename__ = "exam_questions"

    exam_subject_id = Column(Uuid(as_uuid=True), ForeignKey("exam_subjects.id"), nullable=False)
    question_no = Column(Integer, nullable=False)           # 题号
    question_type = Column(String(50), default="")          # 题型：选择题/填空题/解答题
    full_score = Column(Float, nullable=False)               # 该题满分
    knowledge_point_id = Column(Uuid(as_uuid=True), ForeignKey("subject_knowledge_points.id"), nullable=True)
    difficulty = Column(Float, nullable=True)                # 预设难度系数 0~1
    cognitive_level = Column(String(50), default="")         # 认知层次：识记/理解/应用/综合
    estimated_pass_rate = Column(Float, nullable=True)       # 预估得分率
    content = Column(Text, default="")                       # 题目内容（可选）

    exam_subject = relationship("ExamSubject", back_populates="exam_questions")
    knowledge_point = relationship("SubjectKnowledgePoint")

    __table_args__ = (
        UniqueConstraint("exam_subject_id", "question_no", name="uq_exam_question_no"),
    )


class ScoreDetail(BaseModel):
    """学生小题分 —— 学生在某道小题上的得分"""
    __tablename__ = "score_details"

    score_id = Column(Uuid(as_uuid=True), ForeignKey("scores.id"), nullable=False)
    question_id = Column(Uuid(as_uuid=True), ForeignKey("exam_questions.id"), nullable=False)
    score_value = Column(Float, nullable=False, default=0)   # 该题实际得分

    score = relationship("Score", back_populates="score_details")
    question = relationship("ExamQuestion")

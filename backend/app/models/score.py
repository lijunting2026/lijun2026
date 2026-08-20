from sqlalchemy import Column, Float, ForeignKey, String, Index
from sqlalchemy.types import Uuid
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Score(BaseModel):
    __tablename__ = "scores"
    __table_args__ = (
        Index("idx_scores_student_id", "student_id"),
        Index("idx_scores_exam_subject_id", "exam_subject_id"),
        Index("idx_scores_class_id", "class_id"),
        Index("idx_scores_student_exam", "student_id", "exam_subject_id", unique=True),
    )
    student_id = Column(Uuid(as_uuid=True), ForeignKey("students.id"), nullable=False)
    exam_subject_id = Column(Uuid(as_uuid=True), ForeignKey("exam_subjects.id"), nullable=False)
    score_value = Column(Float, nullable=False)
    status = Column(String(20), default="normal")
    class_id = Column(Uuid(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    student = relationship("Student", back_populates="scores")
    exam_subject = relationship("ExamSubject", back_populates="scores")
    class_info = relationship("ClassInfo")
    score_details = relationship("ScoreDetail", back_populates="score", cascade="all, delete-orphan")

from sqlalchemy import Column, String, Date, Float, ForeignKey
from sqlalchemy.types import Uuid
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Exam(BaseModel):
    __tablename__ = "exams"
    name = Column(String(200), nullable=False)
    exam_date = Column(Date, nullable=False)
    exam_type = Column(String(50), default="月考")
    grade_id = Column(Uuid(as_uuid=True), ForeignKey("grades.id"), nullable=False)
    grade = relationship("Grade")
    exam_subjects = relationship("ExamSubject", back_populates="exam", cascade="all, delete-orphan")

class ExamSubject(BaseModel):
    __tablename__ = "exam_subjects"
    exam_id = Column(Uuid(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    subject_id = Column(Uuid(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    full_score = Column(Float, nullable=False)
    weight = Column(Float, default=1.0)
    exam = relationship("Exam", back_populates="exam_subjects")
    subject = relationship("Subject", back_populates="exam_subjects")
    scores = relationship("Score", back_populates="exam_subject", cascade="all, delete-orphan")

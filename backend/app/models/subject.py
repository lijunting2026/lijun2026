from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Subject(BaseModel):
    __tablename__ = "subjects"
    name = Column(String(50), nullable=False, unique=True)
    full_score = Column(Float, nullable=False, default=100)
    sort_order = Column(Integer, default=0)
    exam_subjects = relationship("ExamSubject", back_populates="subject", cascade="all, delete-orphan")

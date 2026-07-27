from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.types import Uuid
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Grade(BaseModel):
    __tablename__ = "grades"
    name = Column(String(50), nullable=False, unique=True)
    sort_order = Column(Integer, default=0)
    classes = relationship("ClassInfo", back_populates="grade", cascade="all, delete-orphan")

class ClassInfo(BaseModel):
    __tablename__ = "classes"
    name = Column(String(50), nullable=False)
    grade_id = Column(Uuid(as_uuid=True), ForeignKey("grades.id"), nullable=False)
    grade = relationship("Grade", back_populates="classes")
    students = relationship("Student", back_populates="class_info", cascade="all, delete-orphan")

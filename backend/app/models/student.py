from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.types import Uuid
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Student(BaseModel):
    __tablename__ = "students"
    student_no = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    gender = Column(String(10), default="未知")
    class_id = Column(Uuid(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    class_info = relationship("ClassInfo", back_populates="students")
    scores = relationship("Score", back_populates="student", cascade="all, delete-orphan")

import uuid
from app.utils import parse_uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.school import Grade, ClassInfo
from app.schemas.school import GradeCreate, GradeResponse, ClassCreate, ClassResponse
router = APIRouter(prefix="/schools", tags=["学校管理"])

@router.get("/grades", response_model=List[GradeResponse])
def list_grades(db: Session = Depends(get_db)):
    grades = db.query(Grade).order_by(Grade.sort_order).all()
    return [GradeResponse(id=str(g.id), name=g.name, sort_order=g.sort_order, created_at=g.created_at) for g in grades]

@router.post("/grades", response_model=GradeResponse)
def create_grade(data: GradeCreate, db: Session = Depends(get_db)):
    grade = Grade(name=data.name, sort_order=data.sort_order)
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return GradeResponse(id=str(grade.id), name=grade.name, sort_order=grade.sort_order, created_at=grade.created_at)

@router.put("/grades/{grade_id}", response_model=GradeResponse)
def update_grade(grade_id: str, data: GradeCreate, db: Session = Depends(get_db)):
    grade = db.query(Grade).filter(Grade.id == parse_uuid(grade_id)).first()
    if not grade:
        raise HTTPException(status_code=404, detail="年级不存在")
    existing = db.query(Grade).filter(Grade.name == data.name, Grade.id != parse_uuid(grade_id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="年级名称已存在")
    grade.name = data.name
    grade.sort_order = data.sort_order
    db.commit()
    db.refresh(grade)
    return GradeResponse(id=str(grade.id), name=grade.name, sort_order=grade.sort_order, created_at=grade.created_at)

@router.delete("/grades/{grade_id}")
def delete_grade(grade_id: str, db: Session = Depends(get_db)):
    grade = db.query(Grade).filter(Grade.id == parse_uuid(grade_id)).first()
    if not grade:
        raise HTTPException(status_code=404, detail="年级不存在")
    db.delete(grade)
    db.commit()
    return {"message": "已删除"}

@router.get("/classes", response_model=List[ClassResponse])
def list_classes(grade_id: str = None, db: Session = Depends(get_db)):
    q = db.query(ClassInfo)
    if grade_id:
        q = q.filter(ClassInfo.grade_id == parse_uuid(grade_id))
    classes = q.all()
    result = []
    for c in classes:
        grade_name = c.grade.name if c.grade else None
        student_count = len(c.students) if c.students else 0
        result.append(ClassResponse(id=str(c.id), name=c.name, grade_id=str(c.grade_id), grade_name=grade_name, student_count=student_count, created_at=c.created_at))
    return result

@router.post("/classes", response_model=ClassResponse)
def create_class(data: ClassCreate, db: Session = Depends(get_db)):
    grade = db.query(Grade).filter(Grade.id == parse_uuid(data.grade_id)).first()
    if not grade:
        raise HTTPException(status_code=404, detail="年级不存在")
    cls = ClassInfo(name=data.name, grade_id=parse_uuid(data.grade_id))
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return ClassResponse(id=str(cls.id), name=cls.name, grade_id=str(cls.grade_id), grade_name=grade.name, student_count=0, created_at=cls.created_at)

@router.put("/classes/{class_id}", response_model=ClassResponse)
def update_class(class_id: str, data: ClassCreate, db: Session = Depends(get_db)):
    cls = db.query(ClassInfo).filter(ClassInfo.id == parse_uuid(class_id)).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    grade = db.query(Grade).filter(Grade.id == parse_uuid(data.grade_id)).first()
    if not grade:
        raise HTTPException(status_code=404, detail="年级不存在")
    cls.name = data.name
    cls.grade_id = parse_uuid(data.grade_id)
    db.commit()
    db.refresh(cls)
    grade_name = cls.grade.name if cls.grade else None
    return ClassResponse(id=str(cls.id), name=cls.name, grade_id=str(cls.grade_id), grade_name=grade_name, student_count=0, created_at=cls.created_at)

@router.delete("/classes/{class_id}")
def delete_class(class_id: str, db: Session = Depends(get_db)):
    cls = db.query(ClassInfo).filter(ClassInfo.id == parse_uuid(class_id)).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    db.delete(cls)
    db.commit()
    return {"message": "已删除"}

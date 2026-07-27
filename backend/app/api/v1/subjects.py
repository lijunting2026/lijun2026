import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectResponse
router = APIRouter(prefix="/subjects", tags=["\u79d1\u76ee\u7ba1\u7406"])

@router.get("/", response_model=List[SubjectResponse])
def list_subjects(db: Session = Depends(get_db)):
    subjects = db.query(Subject).order_by(Subject.sort_order).all()
    return [SubjectResponse(id=str(s.id), name=s.name, full_score=s.full_score, sort_order=s.sort_order, created_at=s.created_at) for s in subjects]

@router.post("/", response_model=SubjectResponse)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db)):
    existing = db.query(Subject).filter(Subject.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="\u79d1\u76ee\u5df2\u5b58\u5728")
    subject = Subject(name=data.name, full_score=data.full_score, sort_order=data.sort_order)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return SubjectResponse(id=str(subject.id), name=subject.name, full_score=subject.full_score, sort_order=subject.sort_order, created_at=subject.created_at)

@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(subject_id: str, data: SubjectCreate, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == uuid.UUID(subject_id)).first()
    if not subject:
        raise HTTPException(status_code=404, detail="\u79d1\u76ee\u4e0d\u5b58\u5728")
    existing = db.query(Subject).filter(Subject.name == data.name, Subject.id != uuid.UUID(subject_id)).first()
    if existing:
        raise HTTPException(status_code=400, detail='科目名称已存在')
    subject.name = data.name
    subject.full_score = data.full_score
    subject.sort_order = data.sort_order
    db.commit()
    db.refresh(subject)
    return SubjectResponse(id=str(subject.id), name=subject.name, full_score=subject.full_score, sort_order=subject.sort_order, created_at=subject.created_at)

@router.delete("/{subject_id}")
def delete_subject(subject_id: str, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == uuid.UUID(subject_id)).first()
    if not subject:
        raise HTTPException(status_code=404, detail="\u79d1\u76ee\u4e0d\u5b58\u5728")
    db.delete(subject)
    db.commit()
    return {"message": "\u5df2\u5220\u9664"}

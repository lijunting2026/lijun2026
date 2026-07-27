from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.utils import parse_uuid
from app.core.database import get_db
from app.models.exam import Exam, ExamSubject
from app.models.subject import Subject
from app.schemas.exam import ExamCreate, ExamResponse, ExamSubjectResponse
router = APIRouter(prefix="/exams", tags=["\u8003\u8bd5\u7ba1\u7406"])

@router.get("/", response_model=List[ExamResponse])
def list_exams(grade_id: str = None, exam_type: str = None, db: Session = Depends(get_db)):
    q = db.query(Exam)
    if grade_id:
        q = q.filter(Exam.grade_id == parse_uuid(grade_id))
    if exam_type:
        q = q.filter(Exam.exam_type == exam_type)
    exams = q.order_by(Exam.exam_date.desc()).all()
    result = []
    for e in exams:
        grade_name = e.grade.name if e.grade else None
        subjects = []
        for es in e.exam_subjects:
            subj = db.query(Subject).filter(Subject.id == es.subject_id).first()
            subjects.append(ExamSubjectResponse(id=str(es.id), subject_id=str(es.subject_id), subject_name=subj.name if subj else None, full_score=es.full_score, weight=es.weight))
        result.append(ExamResponse(id=str(e.id), name=e.name, exam_date=e.exam_date, exam_type=e.exam_type, grade_id=str(e.grade_id), grade_name=grade_name, exam_subjects=subjects, created_at=e.created_at))
    return result

@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam(exam_id: str, db: Session = Depends(get_db)):
    e = db.query(Exam).filter(Exam.id == parse_uuid(exam_id)).first()
    if not e:
        raise HTTPException(status_code=404, detail="\u8003\u8bd5\u4e0d\u5b58\u5728")
    grade_name = e.grade.name if e.grade else None
    subjects = []
    for es in e.exam_subjects:
        subj = db.query(Subject).filter(Subject.id == es.subject_id).first()
        subjects.append(ExamSubjectResponse(id=str(es.id), subject_id=str(es.subject_id), subject_name=subj.name if subj else None, full_score=es.full_score, weight=es.weight))
    return ExamResponse(id=str(e.id), name=e.name, exam_date=e.exam_date, exam_type=e.exam_type, grade_id=str(e.grade_id), grade_name=grade_name, exam_subjects=subjects, created_at=e.created_at)

@router.post("/", response_model=ExamResponse)
def create_exam(data: ExamCreate, db: Session = Depends(get_db)):
    exam = Exam(name=data.name, exam_date=data.exam_date, exam_type=data.exam_type, grade_id=data.grade_id)
    db.add(exam)
    db.flush()
    for s in data.subjects:
        es = ExamSubject(exam_id=exam.id, subject_id=s.subject_id, full_score=s.full_score, weight=s.weight)
        db.add(es)
    db.commit()
    db.refresh(exam)
    grade_name = exam.grade.name if exam.grade else None
    subjects = []
    for es in exam.exam_subjects:
        subj = db.query(Subject).filter(Subject.id == es.subject_id).first()
        subjects.append(ExamSubjectResponse(id=str(es.id), subject_id=str(es.subject_id), subject_name=subj.name if subj else None, full_score=es.full_score, weight=es.weight))
    return ExamResponse(id=str(exam.id), name=exam.name, exam_date=exam.exam_date, exam_type=exam.exam_type, grade_id=str(exam.grade_id), grade_name=grade_name, exam_subjects=subjects, created_at=exam.created_at)

@router.delete("/{exam_id}")
def delete_exam(exam_id: str, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == parse_uuid(exam_id)).first()
    if not exam:
        raise HTTPException(status_code=404, detail="\u8003\u8bd5\u4e0d\u5b58\u5728")
    db.delete(exam)
    db.commit()
    return {"message": "\u5df2\u5220\u9664"}


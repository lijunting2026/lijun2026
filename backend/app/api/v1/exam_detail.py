"""知识点库、细目表管理 API"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.exam_detail import SubjectKnowledgePoint, ExamQuestion
from app.models.exam import ExamSubject
from app.schemas.exam_detail import (
    KnowledgePointCreate, KnowledgePointUpdate, KnowledgePointResponse,
    ExamQuestionCreate, ExamQuestionResponse, ExamBlueprintImport,
)
import uuid
from typing import List

router = APIRouter(prefix="/knowledge-points", tags=["知识点管理"])


def _build_kp_tree(kps: List[SubjectKnowledgePoint], parent_id=None) -> List[dict]:
    """将知识点列表转换为树形结构"""
    result = []
    for kp in kps:
        if kp.parent_id == parent_id:
            children = _build_kp_tree(kps, kp.id)
            result.append({
                "id": str(kp.id),
                "subject_id": str(kp.subject_id),
                "name": kp.name,
                "parent_id": str(kp.parent_id) if kp.parent_id else None,
                "sort_order": kp.sort_order,
                "description": kp.description or "",
                "children": children,
            })
    return result


@router.get("/tree/{subject_id}")
def get_knowledge_tree(subject_id: str, db: Session = Depends(get_db)):
    """获取某个科目的知识点树"""
    kps = db.query(SubjectKnowledgePoint).filter(
        SubjectKnowledgePoint.subject_id == uuid.UUID(subject_id)
    ).order_by(SubjectKnowledgePoint.sort_order).all()
    return _build_kp_tree(kps)


@router.get("/{subject_id}")
def list_knowledge_points(subject_id: str, db: Session = Depends(get_db)):
    """获取某个科目的知识点列表（扁平）"""
    kps = db.query(SubjectKnowledgePoint).filter(
        SubjectKnowledgePoint.subject_id == uuid.UUID(subject_id)
    ).order_by(SubjectKnowledgePoint.sort_order).all()
    return [{
        "id": str(kp.id),
        "subject_id": str(kp.subject_id),
        "name": kp.name,
        "parent_id": str(kp.parent_id) if kp.parent_id else None,
        "sort_order": kp.sort_order,
        "description": kp.description or "",
    } for kp in kps]


@router.post("/")
def create_knowledge_point(
    data: KnowledgePointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可管理知识点")
    kp = SubjectKnowledgePoint(
        subject_id=uuid.UUID(data.subject_id),
        name=data.name,
        parent_id=uuid.UUID(data.parent_id) if data.parent_id else None,
        sort_order=data.sort_order,
        description=data.description,
    )
    db.add(kp)
    db.commit()
    db.refresh(kp)
    return {"id": str(kp.id), "message": "创建成功"}


@router.put("/{kp_id}")
def update_knowledge_point(
    kp_id: str,
    data: KnowledgePointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可管理知识点")
    kp = db.query(SubjectKnowledgePoint).filter(
        SubjectKnowledgePoint.id == uuid.UUID(kp_id)
    ).first()
    if not kp:
        raise HTTPException(status_code=404, detail="知识点不存在")
    if data.name is not None:
        kp.name = data.name
    if data.parent_id is not None:
        kp.parent_id = uuid.UUID(data.parent_id) if data.parent_id else None
    if data.sort_order is not None:
        kp.sort_order = data.sort_order
    if data.description is not None:
        kp.description = data.description
    db.commit()
    return {"message": "更新成功"}


@router.delete("/{kp_id}")
def delete_knowledge_point(
    kp_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可管理知识点")
    kp = db.query(SubjectKnowledgePoint).filter(
        SubjectKnowledgePoint.id == uuid.UUID(kp_id)
    ).first()
    if not kp:
        raise HTTPException(status_code=404, detail="知识点不存在")
    # Also delete children
    children = db.query(SubjectKnowledgePoint).filter(
        SubjectKnowledgePoint.parent_id == uuid.UUID(kp_id)
    ).all()
    for c in children:
        db.delete(c)
    db.delete(kp)
    db.commit()
    return {"message": "已删除"}


@router.post("/import-blueprint")
def import_exam_blueprint(
    data: ExamBlueprintImport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导入命题细目表"""
    es = db.query(ExamSubject).filter(
        ExamSubject.id == uuid.UUID(data.exam_subject_id)
    ).first()
    if not es:
        raise HTTPException(status_code=404, detail="考试科目不存在")

    # Update exam subject quality metrics
    if data.difficulty is not None:
        es.difficulty = data.difficulty
    if data.discrimination is not None:
        es.discrimination = data.discrimination
    if data.reliability is not None:
        es.reliability = data.reliability

    # Clear existing questions and recreate
    db.query(ExamQuestion).filter(
        ExamQuestion.exam_subject_id == uuid.UUID(data.exam_subject_id)
    ).delete()

    for q in data.questions:
        eq = ExamQuestion(
            exam_subject_id=uuid.UUID(data.exam_subject_id),
            question_no=q.question_no,
            question_type=q.question_type,
            full_score=q.full_score,
            knowledge_point_id=uuid.UUID(q.knowledge_point_id) if q.knowledge_point_id else None,
            difficulty=q.difficulty,
            cognitive_level=q.cognitive_level,
            estimated_pass_rate=q.estimated_pass_rate,
            content=q.content,
        )
        db.add(eq)

    db.commit()
    return {"message": f"已导入 {len(data.questions)} 道小题的细目表"}


@router.get("/exam-questions/{exam_subject_id}")
def get_exam_questions(exam_subject_id: str, db: Session = Depends(get_db)):
    """获取某科目下的所有小题定义"""
    questions = db.query(ExamQuestion).filter(
        ExamQuestion.exam_subject_id == uuid.UUID(exam_subject_id)
    ).order_by(ExamQuestion.question_no).all()

    result = []
    for q in questions:
        kp_name = None
        if q.knowledge_point_id:
            kp = db.query(SubjectKnowledgePoint).filter(
                SubjectKnowledgePoint.id == q.knowledge_point_id
            ).first()
            kp_name = kp.name if kp else None
        result.append({
            "id": str(q.id),
            "exam_subject_id": str(q.exam_subject_id),
            "question_no": q.question_no,
            "question_type": q.question_type,
            "full_score": q.full_score,
            "knowledge_point_id": str(q.knowledge_point_id) if q.knowledge_point_id else None,
            "knowledge_point_name": kp_name,
            "difficulty": q.difficulty,
            "cognitive_level": q.cognitive_level,
            "estimated_pass_rate": q.estimated_pass_rate,
            "content": q.content,
        })
    return result

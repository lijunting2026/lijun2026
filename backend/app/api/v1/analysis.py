from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.analytics.analysis_service import AnalysisService
from app.services.analytics.dashboard_service import DashboardService
from app.services.analytics.student_tracking import StudentTrackingService, ClassAnalysisService


router = APIRouter(prefix="/analysis", tags=["数据分析"])


@router.get("/exam/{exam_id}")
def analyze_exam(exam_id: str, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    return service.get_exam_analysis(exam_id)


@router.get("/distribution/{exam_subject_id}")
def get_distribution(exam_subject_id: str, bins: int = 10, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    return service.get_score_distribution(exam_subject_id, bins)


@router.get("/student/{student_id}")
def get_student_analysis(student_id: str, db: Session = Depends(get_db)):
    try:
        service = StudentTrackingService(db)
        result = service.get_student_scores(student_id)
        if not result:
            raise HTTPException(status_code=404, detail="学生不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{student_id}/advice")
def get_student_advice(student_id: str, db: Session = Depends(get_db)):
    try:
        service = StudentTrackingService(db)
        result = service.generate_advice(student_id)
        if not result:
            raise HTTPException(status_code=404, detail="学生不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class/{class_id}")
def get_class_analysis(class_id: str, db: Session = Depends(get_db)):
    try:
        service = ClassAnalysisService(db)
        result = service.get_class_overview(class_id)
        if not result:
            raise HTTPException(status_code=404, detail="班级不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    try:
        service = DashboardService(db)
        return service.get_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
def ai_chat(data: dict, db: Session = Depends(get_db)):
    from app.services.ai.chat_service import AIChatService
    try:
        message = data.get("message", "")
        context_type = data.get("context_type", "general")
        context_id = data.get("context_id")
        service = AIChatService(db)
        result = service.chat(message, context_type, context_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
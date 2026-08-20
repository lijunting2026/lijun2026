"""错题集生成服务 —— 根据学生小题分自动生成错题集"""
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.score import Score
from app.models.exam import Exam, ExamSubject
from app.models.exam_detail import ExamQuestion, ScoreDetail, SubjectKnowledgePoint
from app.models.student import Student
from app.models.subject import Subject
from app.utils import parse_uuid


class ErrorNotebookService:
    """错题集服务 —— 基于小题分找出做错的题目"""

    def __init__(self, db: Session):
        self.db = db

    def generate_error_notebook(self, student_id: str, exam_id: str = None) -> Dict[str, Any]:
        """生成学生错题集"""
        student_uuid = parse_uuid(student_id, "学生ID")
        student = self.db.query(Student).filter(Student.id == student_uuid).first()
        if not student:
            return {"student_name": "", "errors": [], "total_errors": 0, "knowledge_summary": []}

        # Find exams
        q = self.db.query(Exam)
        if exam_id:
            q = q.filter(Exam.id == parse_uuid(exam_id, "考试ID"))
        elif student.class_info and student.class_info.grade_id:
            q = q.filter(Exam.grade_id == student.class_info.grade_id)
        exams = q.order_by(Exam.exam_date.desc()).all()
        if not exams:
            return {"student_name": student.name, "errors": [], "total_errors": 0, "knowledge_summary": []}

        es_list = self.db.query(ExamSubject).filter(
            ExamSubject.exam_id.in_([e.id for e in exams])
        ).all()
        es_ids = [es.id for es in es_list]

        # Get questions with full_score > 0
        questions = self.db.query(ExamQuestion).filter(
            ExamQuestion.exam_subject_id.in_(es_ids),
            ExamQuestion.full_score > 0,
        ).all()
        if not questions:
            return {"student_name": student.name, "errors": [], "total_errors": 0, "knowledge_summary": []}

        q_map = {q.id: q for q in questions}
        q_ids = list(q_map.keys())

        # Get student scores
        scores = self.db.query(Score).filter(
            Score.exam_subject_id.in_(es_ids),
            Score.student_id == student_uuid,
        ).all()
        score_ids = [s.id for s in scores]
        if not score_ids:
            return {"student_name": student.name, "errors": [], "total_errors": 0, "knowledge_summary": []}

        # Get score details
        details = self.db.query(ScoreDetail).filter(
            ScoreDetail.score_id.in_(score_ids),
            ScoreDetail.question_id.in_(q_ids),
        ).all()

        if not details:
            return {"student_name": student.name, "errors": [], "total_errors": 0, "knowledge_summary": []}

        # Build exam_subject -> exam name map
        es_exam_map = {}
        exam_map = {str(e.id): e.name for e in exams}
        for es in es_list:
            es_exam_map[es.id] = exam_map.get(str(es.exam_id), "")

        # Build subject name map
        subj_map = {}
        for es in es_list:
            subj = self.db.query(Subject).filter(Subject.id == es.subject_id).first()
            if subj:
                subj_map[es.id] = subj.name

        # Find errors (score < 60% of full_score)
        errors = []
        kp_error_count: Dict[str, Dict] = {}
        kp_wrong_qs: Dict[str, set] = {}

        for d in details:
            q = q_map.get(d.question_id)
            if not q or q.full_score <= 0:
                continue
            # Determine if this is an error (score < 60%)
            is_error = d.score_value < q.full_score * 0.6
            if not is_error:
                continue

            # Find which exam this score belongs to
            score_obj = next((s for s in scores if s.id == d.score_id), None)
            if not score_obj:
                continue

            exam_name = es_exam_map.get(score_obj.exam_subject_id, "")
            subject_name = subj_map.get(score_obj.exam_subject_id, "")

            # Get knowledge point name
            kp_name = ""
            kp_id_str = ""
            if q.knowledge_point_id:
                kp = self.db.query(SubjectKnowledgePoint).filter(
                    SubjectKnowledgePoint.id == q.knowledge_point_id
                ).first()
                if kp:
                    kp_name = kp.name
                    kp_id_str = str(kp.id)

            errors.append({
                "exam_name": exam_name,
                "subject_name": subject_name,
                "question_no": q.question_no,
                "question_type": q.question_type,
                "question_content": q.content or "",
                "full_score": q.full_score,
                "score_earned": d.score_value,
                "loss_rate": round((q.full_score - d.score_value) / q.full_score * 100, 1),
                "knowledge_point_id": kp_id_str,
                "knowledge_point_name": kp_name,
                "cognitive_level": q.cognitive_level or "",
                "difficulty": q.difficulty,
            })

            # Track per-knowledge-point
            if kp_id_str:
                if kp_id_str not in kp_error_count:
                    kp_error_count[kp_id_str] = {
                        "knowledge_point_name": kp_name,
                        "error_count": 0,
                        "total_loss": 0.0,
                    }
                kp_error_count[kp_id_str]["error_count"] += 1
                kp_error_count[kp_id_str]["total_loss"] += q.full_score - d.score_value

        # Knowledge point summary (sorted by most errors)
        knowledge_summary = sorted(
            [
                {
                    "knowledge_point_name": v["knowledge_point_name"],
                    "error_count": v["error_count"],
                    "total_loss_score": round(v["total_loss"], 1),
                }
                for v in kp_error_count.values()
            ],
            key=lambda x: x["error_count"],
            reverse=True,
        )

        return {
            "student_name": student.name,
            "student_no": student.student_no,
            "total_errors": len(errors),
            "knowledge_summary": knowledge_summary,
            "errors": errors,
        }

from typing import List, Dict, Any, Optional
import uuid
import math
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.exam import Exam, ExamSubject
from app.models.score import Score
from app.models.student import Student
from app.models.subject import Subject
from app.models.school import Grade, ClassInfo
from app.services.analytics.analysis_service import TTLCache


class DashboardService:
    _cache = TTLCache(ttl_seconds=60)

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self) -> Dict[str, Any]:
        cache_key = "dashboard"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        grade_count = self.db.query(Grade).count()
        class_count = self.db.query(ClassInfo).count()
        subject_count = self.db.query(Subject).count()
        student_count = self.db.query(Student).count()
        exam_count = self.db.query(Exam).count()
        score_count = self.db.query(Score).count()

        # Exam type breakdown
        exam_type_rows = self.db.query(Exam.exam_type, func.count(Exam.id)).group_by(Exam.exam_type).all()
        exam_type_map = {"月考": "monthly", "期中": "midterm", "期末": "final"}
        exam_type_stats = {"monthly": 0, "midterm": 0, "final": 0}
        for et, cnt in exam_type_rows:
            key = exam_type_map.get(et)
            if key:
                exam_type_stats[key] = cnt

        # Recent exams
        recent_exams = self.db.query(Exam).order_by(Exam.exam_date.desc()).limit(5).all()
        exam_ids = [e.id for e in recent_exams]
        all_es = self.db.query(ExamSubject).filter(ExamSubject.exam_id.in_(exam_ids)).all() if exam_ids else []
        es_by_exam = {}
        for es in all_es:
            es_by_exam.setdefault(es.exam_id, []).append(es)
        es_ids = [es.id for es in all_es]
        all_scores = self.db.query(Score).filter(Score.exam_subject_id.in_(es_ids)).all() if es_ids else []
        scores_by_es = {}
        for sc in all_scores:
            scores_by_es.setdefault(sc.exam_subject_id, []).append(sc)

        exams_data = []
        for e in recent_exams:
            es_list = es_by_exam.get(e.id, [])
            all_rates = []
            total_students = set()
            for es in es_list:
                scores = scores_by_es.get(es.id, [])
                if scores and es.full_score:
                    avg = sum(s.score_value for s in scores) / len(scores)
                    all_rates.append(round(avg / es.full_score * 100, 1))
                    total_students.update(s.student_id for s in scores)
            avg_rate = round(sum(all_rates) / len(all_rates), 1) if all_rates else 0
            exams_data.append({
                "exam_name": e.name,
                "exam_date": str(e.exam_date) if e.exam_date else "",
                "avg_rate": avg_rate,
                "student_count": len(total_students),
            })

        # Subject stats
        subject_rows = (
            self.db.query(
                Subject.id, Subject.name, Subject.full_score,
                func.avg(Score.score_value).label("avg_score"),
                func.max(Score.score_value).label("max_score"),
                func.count(Score.id).label("score_count"),
            )
            .select_from(Subject)
            .outerjoin(ExamSubject, ExamSubject.subject_id == Subject.id)
            .outerjoin(Score, Score.exam_subject_id == ExamSubject.id)
            .group_by(Subject.id, Subject.name, Subject.full_score)
            .order_by(Subject.sort_order)
        ).all()
        subject_stats = []
        for row in subject_rows:
            if row.score_count and row.score_count > 0:
                subject_stats.append({
                    "subject_name": row.name,
                    "full_score": row.full_score,
                    "avg_score": round(float(row.avg_score), 1),
                    "max_score": float(row.max_score),
                    "count": row.score_count,
                })

        # Trend
        trend_direction = "stable"
        trend_desc = "成绩基本稳定"
        if len(exams_data) >= 2:
            first_rate = exams_data[-1]["avg_rate"]
            last_rate = exams_data[0]["avg_rate"]
            if last_rate > first_rate + 2:
                trend_direction = "up"
                trend_desc = "成绩稳步上升"
            elif last_rate < first_rate - 2:
                trend_direction = "down"
                trend_desc = "成绩有所下降"

        # Risk students
        risk_rows = (
            self.db.query(
                Student.id, Student.name, Student.student_no,
                (func.sum(Score.score_value * 100.0 / ExamSubject.full_score) / func.count(Score.id)).label("avg_rate"),
            )
            .select_from(Student)
            .join(Score, Score.student_id == Student.id)
            .join(ExamSubject, ExamSubject.id == Score.exam_subject_id)
            .filter(ExamSubject.full_score > 0)
            .group_by(Student.id, Student.name, Student.student_no)
            .order_by(func.avg(Score.score_value * 100.0 / ExamSubject.full_score))
            .limit(5)
        ).all()
        risk_students = [
            {"student_name": r.name, "student_no": r.student_no,
             "avg_rate": round(float(r.avg_rate), 1)}
            for r in risk_rows
        ]

        # Subject alerts
        subject_alerts = []
        for ss in subject_stats:
            rate = ss["avg_score"] / ss["full_score"] * 100 if ss["full_score"] and ss["avg_score"] else 100
            if rate < 60:
                subject_alerts.append({
                    "subject_name": ss["subject_name"],
                    "avg_score": ss["avg_score"],
                    "level": "danger" if rate < 45 else "warning",
                    "desc": "得分率偏低" if rate < 45 else "需加强",
                })

        # Class ranking
        class_rows = (
            self.db.query(
                Grade.name.label("grade_name"), Grade.sort_order,
                ClassInfo.id.label("class_id"), ClassInfo.name.label("class_name"),
                (func.sum(Score.score_value * 100.0 / ExamSubject.full_score) / func.count(Score.id)).label("avg_rate"),
            )
            .select_from(Grade)
            .join(ClassInfo, ClassInfo.grade_id == Grade.id)
            .join(Score, Score.class_id == ClassInfo.id)
            .join(ExamSubject, ExamSubject.id == Score.exam_subject_id)
            .filter(ExamSubject.full_score > 0)
            .group_by(Grade.id, Grade.name, Grade.sort_order, ClassInfo.id, ClassInfo.name)
            .order_by(Grade.sort_order)
        ).all()
        class_ranking_dict = {}
        for row in class_rows:
            class_ranking_dict.setdefault(row.grade_name, []).append({
                "class_name": row.class_name,
                "avg_rate": round(float(row.avg_rate), 1),
            })
        for grade_name in list(class_ranking_dict.keys()):
            class_ranking_dict[grade_name].sort(key=lambda x: x["avg_rate"], reverse=True)
        class_ranking = [{"grade_name": gn, "classes": cl} for gn, cl in class_ranking_dict.items()]

        result = {
            "stats": {
                "grades": grade_count, "classes": class_count, "subjects": subject_count,
                "students": student_count, "exams": exam_count, "scores": score_count,
            },
            "recent_exams": exams_data,
            "subject_stats": subject_stats,
            "trend": {"direction": trend_direction, "description": trend_desc},
            "risk_students": risk_students,
            "subject_alerts": subject_alerts,
            "class_ranking": class_ranking,
            "exam_type_stats": exam_type_stats,
        }
        self._cache.set(cache_key, result)
        return result
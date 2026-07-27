from typing import List, Dict, Any, Optional
import uuid
import math
import time
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.exam import Exam, ExamSubject
from app.models.score import Score
from app.models.student import Student
from app.models.subject import Subject
from app.models.school import Grade, ClassInfo


class TTLCache:
    """Thread-safe TTL cache using instance-level storage."""
    def __init__(self, ttl_seconds: int = 60):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        ts = self._timestamps.get(key)
        if ts is not None and (time.time() - ts) < self._ttl:
            return self._cache.get(key)
        return None

    def set(self, key: str, value: Any):
        self._cache[key] = value
        self._timestamps[key] = time.time()

    def invalidate(self, key: str):
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)


class AnalysisService:

    def __init__(self, db: Session):
        self.db = db

    def get_exam_analysis(self, exam_id: str) -> Dict[str, Any]:
        exam_uuid = uuid.UUID(exam_id) if exam_id else None
        exam = self.db.query(Exam).filter(Exam.id == exam_uuid).first()
        if not exam:
            return {}
        exam_subjects = self.db.query(ExamSubject).filter(ExamSubject.exam_id == exam_uuid).all()
        if not exam_subjects:
            return {"exam_id": exam_id, "exam_name": exam.name, "exam_date": str(exam.exam_date) if exam.exam_date else None, "total_students": 0, "grade_stats": [], "class_stats": []}
        es_ids = [es.id for es in exam_subjects]

        # Build subject_id -> ExamSubject map
        es_map = {es.subject_id: es for es in exam_subjects}
        subj_map = {}
        for es in exam_subjects:
            subj = self.db.query(Subject).filter(Subject.id == es.subject_id).first()
            subj_map[es.subject_id] = subj

        # Grade stats - single query with GROUP BY
        grade_rows = (
            self.db.query(
                Score.exam_subject_id,
                func.avg(Score.score_value).label("avg_score"),
                func.max(Score.score_value).label("max_score"),
                func.min(Score.score_value).label("min_score"),
                func.count(Score.id).label("count"),
                func.sum(case((Score.score_value >= ExamSubject.full_score * 0.6, 1), else_=0)).label("passed"),
                func.sum(case((Score.score_value >= ExamSubject.full_score * 0.85, 1), else_=0)).label("excellent"),
            )
            .join(ExamSubject, ExamSubject.id == Score.exam_subject_id)
            .filter(Score.exam_subject_id.in_(es_ids))
            .group_by(Score.exam_subject_id)
        ).all()
        grade_rows_map = {r.exam_subject_id: r for r in grade_rows}

        total_student_ids = set()
        all_score_rows = self.db.query(Score.student_id, Score.class_id, Score.exam_subject_id, Score.score_value).filter(
            Score.exam_subject_id.in_(es_ids)
        ).all()
        for r in all_score_rows:
            total_student_ids.add(r.student_id)
        total_students = len(total_student_ids)

        # Build per-student per-exam_subject score lookup
        score_lookup = {}
        class_student_set = {}
        for r in all_score_rows:
            key = (r.student_id, r.exam_subject_id)
            score_lookup[key] = r.score_value
            class_student_set.setdefault(r.class_id, set()).add(r.student_id)

        grade_stats = []
        for es in exam_subjects:
            sid = es.subject_id
            subj = subj_map.get(sid)
            gr = grade_rows_map.get(es.id)
            count = gr.count if gr and gr.count else 0
            if count == 0:
                continue
            avg_score = float(gr.avg_score) if gr.avg_score else 0
            max_score = float(gr.max_score) if gr.max_score else 0
            min_score = float(gr.min_score) if gr.min_score else 0
            passed = int(gr.passed) if gr.passed else 0
            excellent = int(gr.excellent) if gr.excellent else 0
            # std_dev from loaded scores (SQLite doesn't support stddev_samp easily)
            values = [r.score_value for r in all_score_rows if r.exam_subject_id == es.id]
            variance = sum((v - avg_score) ** 2 for v in values) / count if values else 0
            grade_stats.append({
                "subject_id": str(sid),
                "subject_name": subj.name if subj else "",
                "full_score": es.full_score,
                "avg_score": round(avg_score, 2),
                "max_score": max_score,
                "min_score": min_score,
                "pass_rate": round(passed / count * 100, 2),
                "excellent_rate": round(excellent / count * 100, 2),
                "std_dev": round(math.sqrt(variance), 2),
                "avg_score_rate": round(avg_score / es.full_score * 100, 2) if es.full_score else 0,
            })

        # Class stats - use loaded scores
        classes = self.db.query(ClassInfo).filter(ClassInfo.grade_id == exam.grade_id).all()
        class_stats = []
        for cls in classes:
            cls_student_ids = class_student_set.get(cls.id, set())
            cls_subject_stats = []
            for gs in grade_stats:
                es = es_map.get(uuid.UUID(gs["subject_id"])) if gs["subject_id"] else None
                if not es:
                    continue
                cls_scores = [r.score_value for r in all_score_rows if r.class_id == cls.id and r.exam_subject_id == es.id]
                if not cls_scores:
                    continue
                c_avg = sum(cls_scores) / len(cls_scores)
                c_passed = sum(1 for v in cls_scores if v >= gs["full_score"] * 0.6)
                c_excellent = sum(1 for v in cls_scores if v >= gs["full_score"] * 0.85)
                cls_subject_stats.append({
                    "subject_id": gs["subject_id"],
                    "subject_name": gs["subject_name"],
                    "full_score": gs["full_score"],
                    "avg_score": round(c_avg, 2),
                    "max_score": max(cls_scores),
                    "min_score": min(cls_scores),
                    "pass_rate": round(c_passed / len(cls_scores) * 100, 2),
                    "excellent_rate": round(c_excellent / len(cls_scores) * 100, 2),
                    "std_dev": round(math.sqrt(sum((v - c_avg) ** 2 for v in cls_scores) / len(cls_scores)), 2),
                    "avg_score_rate": round(c_avg / gs["full_score"] * 100, 2) if gs["full_score"] else 0,
                })
            class_stats.append({
                "class_id": str(cls.id),
                "class_name": cls.name,
                "student_count": len(cls_student_ids),
                "stats": cls_subject_stats,
            })

        return {
            "exam_id": exam_id,
            "exam_name": exam.name,
            "exam_date": str(exam.exam_date) if exam.exam_date else None,
            "total_students": total_students,
            "grade_stats": grade_stats,
            "class_stats": class_stats,
        }

    def get_score_distribution(self, exam_subject_id: str, bins: int = 10) -> Dict[str, Any]:
        es_id = uuid.UUID(exam_subject_id)
        es = self.db.query(ExamSubject).filter(ExamSubject.id == es_id).first()
        if not es:
            return {}
        subject = self.db.query(Subject).filter(Subject.id == es.subject_id).first()
        scores = self.db.query(Score).filter(Score.exam_subject_id == es_id).all()
        values = [s.score_value for s in scores]
        if not values:
            return {"subject_id": exam_subject_id, "subject_name": subject.name if subject else "", "distributions": []}

        max_val = es.full_score
        step = max_val / bins
        distribution = []
        for i in range(bins):
            low = round(i * step, 1)
            high = round((i + 1) * step, 1)
            count = sum(1 for v in values if low <= v < high) if i < bins - 1 else sum(1 for v in values if low <= v <= high)
            distribution.append({
                "range_label": f"{low}-{high}",
                "count": count,
                "percentage": round(count / len(values) * 100, 1),
            })

        return {
            "subject_id": exam_subject_id,
            "subject_name": subject.name if subject else "",
            "distributions": distribution,
        }
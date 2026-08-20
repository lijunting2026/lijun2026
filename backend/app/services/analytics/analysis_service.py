from typing import List, Dict, Any, Optional
import uuid
import math
import time
from collections import Counter
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

    # ---------- 辅助方法 ----------

    def _resolve_score_mode(self, exam_subjects: List[ExamSubject], mode: str) -> str:
        """根据数据完整度解析实际使用的分数口径。

        raw=原始分 | converted=赋分 | both=双轨 | auto=按数据完整度降级
        auto 降级规则：存在已配置赋分科目且有赋分数据 -> converted，否则 raw。
        """
        if mode not in ("raw", "converted", "both", "auto"):
            mode = "auto"
        if mode == "auto":
            converted_es = [es for es in exam_subjects if es.scoring_type == "converted"]
            for es in converted_es:
                cnt = (
                    self.db.query(Score)
                    .filter(Score.exam_subject_id == es.id, Score.converted_score.isnot(None))
                    .count()
                )
                if cnt > 0:
                    return "converted"
            return "raw"
        return mode

    def _load_score_rows(self, es_ids):
        """加载成绩行：student_id/class_id/exam_subject_id/score_value/converted_score。"""
        return (
            self.db.query(
                Score.student_id,
                Score.class_id,
                Score.exam_subject_id,
                Score.score_value,
                Score.converted_score,
            )
            .filter(Score.exam_subject_id.in_(es_ids))
            .all()
        )

    def _effective_value(self, row, use_converted: bool) -> float:
        """按口径取有效分数：converted 时取赋分，缺赋分自动降级为原始分。"""
        if use_converted and row.converted_score is not None:
            return row.converted_score
        return row.score_value

    def _subject_stats(self, sid, subj, es, values: List[float]) -> Dict[str, Any]:
        count = len(values)
        avg_score = sum(values) / count
        passed = sum(1 for v in values if v >= es.full_score * 0.6)
        excellent = sum(1 for v in values if v >= es.full_score * 0.85)
        variance = sum((v - avg_score) ** 2 for v in values) / count
        return {
            "subject_id": str(sid),
            "subject_name": subj.name if subj else "",
            "full_score": es.full_score,
            "avg_score": round(avg_score, 2),
            "max_score": max(values),
            "min_score": min(values),
            "pass_rate": round(passed / count * 100, 2),
            "excellent_rate": round(excellent / count * 100, 2),
            "std_dev": round(math.sqrt(variance), 2),
            "avg_score_rate": round(avg_score / es.full_score * 100, 2) if es.full_score else 0,
        }

    def _build_student_pivot(self, exam_subjects, mode: str):
        """构造学生维度透视表。

        返回 (student_scores, student_class)：
        - student_scores[student_id][exam_subject_id] = 有效分数
        - student_scores[student_id]["__total__"] = 总分（原始科目原始分 + 赋分科目有效分）
        - student_class[student_id] = class_id
        """
        use_converted = mode == "converted"
        rows = self._load_score_rows([es.id for es in exam_subjects])
        student_scores: Dict[uuid.UUID, Dict[Any, float]] = {}
        student_class: Dict[uuid.UUID, Any] = {}
        for r in rows:
            value = self._effective_value(r, use_converted)
            student_scores.setdefault(r.student_id, {})[r.exam_subject_id] = value
            student_class.setdefault(r.student_id, r.class_id)
        for stu, scores in student_scores.items():
            total = sum(v for k, v in scores.items() if k != "__total__")
            scores["__total__"] = total
        return student_scores, student_class

    # ---------- 考试整体分析 ----------

    def get_exam_analysis(self, exam_id: str, score_mode: str = "auto") -> Dict[str, Any]:
        exam_uuid = uuid.UUID(exam_id) if exam_id else None
        exam = self.db.query(Exam).filter(Exam.id == exam_uuid).first()
        if not exam:
            return {}
        exam_subjects = self.db.query(ExamSubject).filter(ExamSubject.exam_id == exam_uuid).all()
        if not exam_subjects:
            return {"exam_id": exam_id, "exam_name": exam.name, "exam_date": str(exam.exam_date) if exam.exam_date else None, "total_students": 0, "grade_stats": [], "class_stats": []}

        mode = self._resolve_score_mode(exam_subjects, score_mode)
        use_converted = mode == "converted"
        es_map = {es.subject_id: es for es in exam_subjects}
        subj_map = {}
        for es in exam_subjects:
            subj = self.db.query(Subject).filter(Subject.id == es.subject_id).first()
            subj_map[es.subject_id] = subj

        all_score_rows = self._load_score_rows([es.id for es in exam_subjects])
        total_student_ids = set()
        class_student_set = {}
        for r in all_score_rows:
            total_student_ids.add(r.student_id)
            class_student_set.setdefault(r.class_id, set()).add(r.student_id)
        total_students = len(total_student_ids)

        grade_stats = []
        for es in exam_subjects:
            sid = es.subject_id
            subj = subj_map.get(sid)
            values = [self._effective_value(r, use_converted) for r in all_score_rows if r.exam_subject_id == es.id]
            if not values:
                continue
            stats = self._subject_stats(sid, subj, es, values)
            if mode == "both" and es.scoring_type == "converted":
                c_values = [r.converted_score for r in all_score_rows if r.exam_subject_id == es.id and r.converted_score is not None]
                if c_values:
                    c = self._subject_stats(sid, subj, es, c_values)
                    stats["converted_avg_score"] = c["avg_score"]
                    stats["converted_max_score"] = c["max_score"]
                    stats["converted_min_score"] = c["min_score"]
                    stats["converted_pass_rate"] = c["pass_rate"]
                    stats["converted_excellent_rate"] = c["excellent_rate"]
                    stats["converted_std_dev"] = c["std_dev"]
                    stats["converted_avg_score_rate"] = c["avg_score_rate"]
            grade_stats.append(stats)

        classes = self.db.query(ClassInfo).filter(ClassInfo.grade_id == exam.grade_id).all()
        class_stats = []
        for cls in classes:
            cls_student_ids = class_student_set.get(cls.id, set())
            cls_subject_stats = []
            for gs in grade_stats:
                es = es_map.get(uuid.UUID(gs["subject_id"])) if gs["subject_id"] else None
                if not es:
                    continue
                cls_scores = [
                    self._effective_value(r, use_converted)
                    for r in all_score_rows
                    if r.class_id == cls.id and r.exam_subject_id == es.id
                ]
                if not cls_scores:
                    continue
                subj = subj_map.get(es.subject_id)
                c_stats = self._subject_stats(es.subject_id, subj, es, cls_scores)
                if mode == "both" and es.scoring_type == "converted":
                    cc_values = [r.converted_score for r in all_score_rows if r.class_id == cls.id and r.exam_subject_id == es.id and r.converted_score is not None]
                    if cc_values:
                        cc = self._subject_stats(es.subject_id, subj, es, cc_values)
                        c_stats["converted_avg_score"] = cc["avg_score"]
                        c_stats["converted_max_score"] = cc["max_score"]
                        c_stats["converted_min_score"] = cc["min_score"]
                        c_stats["converted_pass_rate"] = cc["pass_rate"]
                        c_stats["converted_excellent_rate"] = cc["excellent_rate"]
                        c_stats["converted_std_dev"] = cc["std_dev"]
                        c_stats["converted_avg_score_rate"] = cc["avg_score_rate"]
                cls_subject_stats.append(c_stats)
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
            "score_mode": mode,
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

    # ---------- 上线统计 ----------

    def get_line_stats(self, exam_id: str, score_mode: str = "auto") -> Dict[str, Any]:
        from app.models.scoring import ScoreLine
        exam_uuid = uuid.UUID(exam_id) if exam_id else None
        exam = self.db.query(Exam).filter(Exam.id == exam_uuid).first()
        if not exam:
            return {}
        exam_subjects = self.db.query(ExamSubject).filter(ExamSubject.exam_id == exam_uuid).all()
        if not exam_subjects:
            return {"exam_id": exam_id, "total_students": 0, "total_lines": [], "subject_lines": [], "dual_lines": []}

        mode = self._resolve_score_mode(exam_subjects, score_mode)
        lines = self.db.query(ScoreLine).filter(ScoreLine.exam_id == exam_uuid).all()
        student_scores, student_class = self._build_student_pivot(exam_subjects, mode)

        classes = self.db.query(ClassInfo).filter(ClassInfo.grade_id == exam.grade_id).all()
        cls_name_map = {c.id: c.name for c in classes}

        def _class_breakdown(counter: Dict[Any, int], total_counter: Dict[Any, int]):
            out = []
            for cid, cnt in counter.items():
                total = total_counter.get(cid, 0)
                out.append({
                    "class_id": str(cid) if cid else None,
                    "class_name": cls_name_map.get(cid) or "",
                    "count": cnt,
                    "total": total,
                    "rate": round(cnt / total * 100, 2) if total else 0,
                })
            return sorted(out, key=lambda x: -x["rate"])

        total_lines = []
        subject_lines = []
        total_count = len(student_scores)
        for line in lines:
            if line.line_type == "total":
                cnt = 0
                cls_cnt, cls_total = {}, {}
                for stu, scores in student_scores.items():
                    cls = student_class.get(stu)
                    cls_total[cls] = cls_total.get(cls, 0) + 1
                    if scores.get("__total__", 0) >= line.score_value:
                        cnt += 1
                        cls_cnt[cls] = cls_cnt.get(cls, 0) + 1
                total_lines.append({
                    "line_id": str(line.id),
                    "line_name": line.line_name,
                    "score_value": line.score_value,
                    "source": line.source,
                    "count": cnt,
                    "total": total_count,
                    "rate": round(cnt / total_count * 100, 2) if total_count else 0,
                    "classes": _class_breakdown(cls_cnt, cls_total),
                })
            else:
                subject = self.db.query(Subject).filter(Subject.id == line.subject_id).first() if line.subject_id else None
                es = next((e for e in exam_subjects if e.subject_id == line.subject_id), None)
                cnt = 0
                cls_cnt, cls_total = {}, {}
                for stu, scores in student_scores.items():
                    cls = student_class.get(stu)
                    cls_total[cls] = cls_total.get(cls, 0) + 1
                    value = scores.get(es.id) if es else None
                    if value is not None and value >= line.score_value:
                        cnt += 1
                        cls_cnt[cls] = cls_cnt.get(cls, 0) + 1
                subject_lines.append({
                    "line_id": str(line.id),
                    "line_name": line.line_name,
                    "score_value": line.score_value,
                    "source": line.source,
                    "subject_id": str(line.subject_id) if line.subject_id else None,
                    "subject_name": subject.name if subject else "",
                    "count": cnt,
                    "total": total_count,
                    "rate": round(cnt / total_count * 100, 2) if total_count else 0,
                    "classes": _class_breakdown(cls_cnt, cls_total),
                })

        # 双上线：总分达线 且 单科达线
        dual_lines = []
        for tl in total_lines:
            for sl in subject_lines:
                es = next((e for e in exam_subjects if str(e.subject_id) == sl.get("subject_id")), None)
                cnt = 0
                for stu, scores in student_scores.items():
                    if scores.get("__total__", 0) >= tl["score_value"]:
                        value = scores.get(es.id) if es else None
                        if value is not None and value >= sl["score_value"]:
                            cnt += 1
                dual_lines.append({
                    "total_line_id": tl["line_id"],
                    "total_line_name": tl["line_name"],
                    "subject_line_id": sl["line_id"],
                    "subject_line_name": sl["line_name"],
                    "subject_name": sl["subject_name"],
                    "count": cnt,
                    "total": total_count,
                    "rate": round(cnt / total_count * 100, 2) if total_count else 0,
                })

        return {
            "exam_id": exam_id,
            "score_mode": mode,
            "total_students": total_count,
            "total_lines": total_lines,
            "subject_lines": subject_lines,
            "dual_lines": dual_lines,
        }

    # ---------- 一分一段表 ----------

    def get_one_point_table(self, exam_id: str, score_mode: str = "auto") -> Dict[str, Any]:
        exam_uuid = uuid.UUID(exam_id) if exam_id else None
        exam = self.db.query(Exam).filter(Exam.id == exam_uuid).first()
        if not exam:
            return {}
        exam_subjects = self.db.query(ExamSubject).filter(ExamSubject.exam_id == exam_uuid).all()
        if not exam_subjects:
            return {"exam_id": exam_id, "total_students": 0, "items": []}

        mode = self._resolve_score_mode(exam_subjects, score_mode)
        student_scores, _ = self._build_student_pivot(exam_subjects, mode)
        totals = [scores["__total__"] for scores in student_scores.values() if scores.get("__total__") is not None]
        total_count = len(totals)
        counter = Counter(int(round(t)) for t in totals)
        if not counter:
            return {"exam_id": exam_id, "score_mode": mode, "total_students": 0, "items": []}

        max_val = max(counter)
        min_val = min(counter)
        items = []
        cumulative = 0
        for score in range(max_val, min_val - 1, -1):
            c = counter.get(score, 0)
            cumulative += c
            items.append({
                "score": score,
                "count": c,
                "cumulative": cumulative,
                "cumulative_rate": round(cumulative / total_count * 100, 2) if total_count else 0,
            })
        return {
            "exam_id": exam_id,
            "score_mode": mode,
            "total_students": total_count,
            "items": items,
        }

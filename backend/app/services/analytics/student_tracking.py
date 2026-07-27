import uuid, math
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.score import Score
from app.models.student import Student
from app.models.exam import Exam, ExamSubject
from app.models.subject import Subject
from app.models.school import ClassInfo
from app.utils import parse_uuid


class StudentTrackingService:
    def __init__(self, db: Session):
        self.db = db

    def get_student_scores(self, student_id: str) -> Dict[str, Any]:
        student_uuid = parse_uuid(student_id, "学生ID")
        student = self.db.query(Student).filter(Student.id == student_uuid).first()
        if not student:
            return None

        class_name = student.class_info.name if student.class_info else ""
        grade_name = student.class_info.grade.name if student.class_info and student.class_info.grade else ""
        grade_id = student.class_info.grade_id if student.class_info else None

        query = self.db.query(Exam)
        if grade_id:
            query = query.filter(Exam.grade_id == grade_id)
        exams = query.order_by(Exam.exam_date).all()

        subjects = self.db.query(Subject).order_by(Subject.sort_order).all()

        if not exams:
            return {
                "student_id": student_id, "student_no": student.student_no,
                "student_name": student.name, "class_name": class_name,
                "grade_name": grade_name, "exam_count": 0, "exams": [],
                "trends": [], "strengths": [], "weaknesses": [],
                "overall_trend": "暂无数据",
            }

        # Batch load all exam_subjects and scores for this student
        exam_ids = [e.id for e in exams]
        exam_subjects = (
            self.db.query(ExamSubject)
            .filter(ExamSubject.exam_id.in_(exam_ids))
            .all()
        )
        es_ids = [es.id for es in exam_subjects]

        scores = (
            self.db.query(Score)
            .filter(
                Score.student_id == student_uuid,
                Score.exam_subject_id.in_(es_ids),
            )
            .all()
        )

        # Build lookup maps
        es_by_exam: Dict[uuid.UUID, List[ExamSubject]] = {}
        for es in exam_subjects:
            es_by_exam.setdefault(es.exam_id, []).append(es)

        score_by_es: Dict[uuid.UUID, Score] = {}
        for sc in scores:
            score_by_es[sc.exam_subject_id] = sc

        subj_map = {s.id: s for s in subjects}

        exam_records = []
        all_score_values = []

        for exam in exams:
            es_list = es_by_exam.get(exam.id, [])
            subject_scores = []
            total_rate = 0.0
            subject_count = 0

            for es in es_list:
                subj = subj_map.get(es.subject_id)
                if not subj:
                    continue
                score = score_by_es.get(es.id)
                score_val = score.score_value if score else None
                rate = (score_val / es.full_score * 100) if score_val is not None and es.full_score else None
                subject_scores.append({
                    "subject_id": str(subj.id),
                    "subject_name": subj.name,
                    "full_score": es.full_score,
                    "score": round(score_val, 1) if score_val is not None else None,
                    "rate": round(rate, 1) if rate is not None else None,
                })
                if rate is not None:
                    total_rate += rate
                    subject_count += 1

            avg_rate = round(total_rate / subject_count, 1) if subject_count > 0 else None
            exam_records.append({
                "exam_id": str(exam.id),
                "exam_name": exam.name,
                "exam_date": str(exam.exam_date) if exam.exam_date else "",
                "exam_type": exam.exam_type,
                "avg_rate": avg_rate,
                "subjects": subject_scores,
            })
            if avg_rate is not None:
                all_score_values.append(avg_rate)

        trends = self._analyze_trends(exam_records, subjects)
        strengths, weaknesses = self._analyze_strengths(exam_records, subjects)

        return {
            "student_id": student_id,
            "student_no": student.student_no,
            "student_name": student.name,
            "class_name": class_name,
            "grade_name": grade_name,
            "exam_count": len(exam_records),
            "exams": exam_records,
            "trends": trends,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "overall_trend": self._overall_trend(all_score_values),
        }

    def _analyze_trends(self, exam_records: List, subjects: List) -> List:
        trends = []
        for subj in subjects:
            scores_over_time = []
            for exam in exam_records:
                for s in exam["subjects"]:
                    if s["subject_id"] == str(subj.id) and s["rate"] is not None:
                        scores_over_time.append({
                            "exam_name": exam["exam_name"],
                            "exam_date": exam["exam_date"],
                            "rate": s["rate"],
                        })
                        break
            if len(scores_over_time) >= 2:
                rates = [s["rate"] for s in scores_over_time]
                mid = len(rates) // 2
                avg_first = sum(rates[:mid]) / mid
                avg_second = sum(rates[mid:]) / (len(rates) - mid)
                diff = avg_second - avg_first
                direction = "up" if diff > 5 else ("down" if diff < -5 else "stable")
                desc = "持续进步" if diff > 10 else ("略有提升" if diff > 5 else ("明显下滑" if diff < -10 else ("略有下降" if diff < -5 else "保持稳定")))
            elif len(scores_over_time) == 1:
                direction, desc = "stable", "仅有单次数据"
            else:
                direction, desc = "unknown", "暂无数据"
            trends.append({
                "subject_id": str(subj.id),
                "subject_name": subj.name,
                "direction": direction,
                "description": desc,
                "scores": scores_over_time,
            })
        return trends

    def _analyze_strengths(self, exam_records: List, subjects: List):
        strengths = []
        weaknesses = []
        for subj in subjects:
            rates = []
            for exam in exam_records:
                for s in exam["subjects"]:
                    if s["subject_id"] == str(subj.id) and s["rate"] is not None:
                        rates.append(s["rate"])
                        break
            if rates:
                avg_rate = sum(rates) / len(rates)
                latest_rate = rates[-1]
                entry = {
                    "subject_id": str(subj.id),
                    "subject_name": subj.name,
                    "avg_rate": round(avg_rate, 1),
                    "latest_rate": round(latest_rate, 1),
                }
                if avg_rate >= 75:
                    strengths.append(entry)
                elif avg_rate < 60:
                    weaknesses.append(entry)
        strengths.sort(key=lambda x: x["avg_rate"], reverse=True)
        weaknesses.sort(key=lambda x: x["avg_rate"])
        return strengths, weaknesses

    def _overall_trend(self, values: List[float]) -> str:
        if len(values) < 2:
            return "暂无趋势" if not values else "仅有一次记录"
        mid = len(values) // 2
        avg_first = sum(values[:mid]) / mid
        avg_last = sum(values[mid:]) / (len(values) - mid)
        diff = avg_last - avg_first
        if diff > 5:
            return "稳步上升"
        elif diff < -5:
            return "有所下降"
        return "保持稳定"

    def generate_advice(self, student_id: str) -> Optional[Dict[str, Any]]:
        data = self.get_student_scores(student_id)
        if not data:
            return None
        t = data.get("overall_trend", "未知")
        items = []
        for s in data.get("weaknesses", []):
            level = (
                "亟待提升" if s["avg_rate"] < 60
                else ("需要加强" if s["avg_rate"] < 75 else "尚有提升空间")
            )
            items.append({
                "category": "薄弱科目-" + s["subject_name"],
                "content": s["subject_name"] + "得分率" + str(s["avg_rate"]) + "%," + level + "。建议回归课本夯实基础，制定每日专项练习，建立错题本定期回顾。",
                "priority": "high" if s["avg_rate"] < 60 else "medium",
            })
        for tr in data.get("trends", []):
            if tr["direction"] == "down":
                items.append({
                    "category": "趋势预警-" + tr["subject_name"],
                    "content": tr["subject_name"] + "成绩呈下滑趋势(" + tr["description"] + ")。建议及时分析原因，增加该科目复习时间。",
                    "priority": "high",
                })
            elif tr["direction"] == "up" and len(tr.get("scores", [])) >= 2:
                items.append({
                    "category": "进步科目-" + tr["subject_name"],
                    "content": tr["subject_name"] + "成绩呈上升趋势，方法值得肯定，建议将好经验应用到其他科目。",
                    "priority": "low",
                })
        return {
            "student_id": student_id,
            "student_name": data["student_name"],
            "overall_trend": t,
            "advice_items": items,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }


class ClassAnalysisService:
    def __init__(self, db: Session):
        self.db = db

    def get_class_overview(self, class_id: str) -> Dict[str, Any]:
        cls_uuid = parse_uuid(class_id, "班级ID")
        cls = self.db.query(ClassInfo).filter(ClassInfo.id == cls_uuid).first()
        if not cls:
            return None

        students = (
            self.db.query(Student)
            .filter(Student.class_id == cls.id)
            .order_by(Student.student_no)
            .all()
        )
        grade_name = cls.grade.name if cls.grade else ""
        exams = (
            self.db.query(Exam)
            .filter(Exam.grade_id == cls.grade_id)
            .order_by(Exam.exam_date)
            .all()
        )
        subjects = self.db.query(Subject).order_by(Subject.sort_order).all()

        if not exams:
            return {
                "class_id": class_id, "class_name": cls.name,
                "grade_name": grade_name, "student_count": len(students),
                "exam_count": len(exams), "student_list": [],
                "exam_summary": [], "subject_stats": [],
                "risk_students": [],
            }

        student_ids = [s.id for s in students]
        exam_ids = [e.id for e in exams]

        # Batch load all exam subjects for these exams
        all_exam_subjects = (
            self.db.query(ExamSubject)
            .filter(ExamSubject.exam_id.in_(exam_ids))
            .all()
        )
        es_ids = [es.id for es in all_exam_subjects]

        # Batch load all scores for this class (by scores.class_id)
        all_scores = (
            self.db.query(Score)
            .filter(
                Score.class_id == cls.id,
                Score.exam_subject_id.in_(es_ids),
            )
            .all()
        )

        # Build lookup maps
        es_by_exam: Dict[uuid.UUID, List[ExamSubject]] = {}
        for es in all_exam_subjects:
            es_by_exam.setdefault(es.exam_id, []).append(es)

        es_map: Dict[uuid.UUID, ExamSubject] = {es.id: es for es in all_exam_subjects}

        scores_by_key: Dict[tuple, float] = {}
        for sc in all_scores:
            scores_by_key[(sc.student_id, sc.exam_subject_id)] = sc.score_value

        # Student list with avg rates
        student_list = []
        for s in students:
            total_rate = 0.0
            count = 0
            for exam in exams:
                for es in es_by_exam.get(exam.id, []):
                    sv = scores_by_key.get((s.id, es.id))
                    if sv is not None and es.full_score:
                        total_rate += sv / es.full_score * 100
                        count += 1
            avg = round(total_rate / count, 1) if count > 0 else None
            student_list.append({
                "student_id": str(s.id),
                "student_no": s.student_no,
                "student_name": s.name,
                "avg_rate": avg,
            })

        # Exam summary
        exam_summary = []
        for exam in exams:
            total_rate = 0.0
            count = 0
            for es in es_by_exam.get(exam.id, []):
                for s in students:
                    sv = scores_by_key.get((s.id, es.id))
                    if sv is not None and es.full_score:
                        total_rate += sv / es.full_score * 100
                        count += 1
            exam_summary.append({
                "exam_id": str(exam.id),
                "exam_name": exam.name,
                "exam_date": str(exam.exam_date) if exam.exam_date else "",
                "avg_rate": round(total_rate / count, 1) if count > 0 else None,
            })

        # Subject stats
        subject_stats = []
        for subj in subjects:
            vals = []
            for exam in exams:
                for es in es_by_exam.get(exam.id, []):
                    if es.subject_id != subj.id:
                        continue
                    for s in students:
                        sv = scores_by_key.get((s.id, es.id))
                        if sv is not None:
                            vals.append(sv)
            if vals:
                subject_stats.append({
                    "subject_name": subj.name,
                    "avg_score": round(sum(vals) / len(vals), 1),
                    "max_score": max(vals),
                    "min_score": min(vals),
                    "count": len(vals),
                })

        # Risk students
        valid = [s for s in student_list if s["avg_rate"] is not None]
        valid.sort(key=lambda x: x["avg_rate"])
        risk_students = valid[:5]

        return {
            "class_id": class_id,
            "class_name": cls.name,
            "grade_name": grade_name,
            "student_count": len(students),
            "exam_count": len(exams),
            "student_list": student_list,
            "exam_summary": exam_summary,
            "subject_stats": subject_stats,
            "risk_students": risk_students,
        }


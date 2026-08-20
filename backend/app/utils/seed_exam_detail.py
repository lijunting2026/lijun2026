"""为已有考试生成细目表和小题分测试数据"""
import random
import math
from datetime import datetime
from app.core.database import SessionLocal
from app.models.exam import Exam, ExamSubject
from app.models.exam_detail import ExamQuestion, ScoreDetail, SubjectKnowledgePoint
from app.models.score import Score
from app.models.subject import Subject

random.seed(12345)  # 固定种子确保可重复

# 各科目题型配置
SUBJECT_QUESTION_CONFIG = {
    "语文": [
        ("选择题", 3, 8),    # 8道选择题，每题3分
        ("选择题", 4, 4),    # 4道选择题，每题4分
        ("填空题", 4, 4),    # 4道填空题，每题4分
        ("文言文阅读", 5, 3),
        ("现代文阅读", 6, 3),
        ("写作", 60, 1),
    ],
    "数学": [
        ("选择题", 5, 8),
        ("选择题", 6, 2),
        ("填空题", 5, 4),
        ("解答题", 10, 2),
        ("解答题", 12, 2),
        ("解答题", 14, 1),
    ],
    "英语": [
        ("阅读理解", 2, 10),
        ("阅读理解", 2.5, 8),
        ("完形填空", 1.5, 10),
        ("语法填空", 1.5, 10),
        ("写作", 25, 1),
        ("读后续写", 25, 1),
    ],
    "物理": [
        ("选择题", 4, 6),
        ("选择题", 5, 2),
        ("填空题", 4, 3),
        ("实验题", 6, 2),
        ("计算题", 8, 2),
        ("计算题", 10, 1),
    ],
    "化学": [
        ("选择题", 3, 8),
        ("选择题", 4, 4),
        ("填空题", 4, 3),
        ("推断题", 8, 2),
        ("计算题", 10, 1),
        ("实验题", 12, 1),
    ],
    "生物": [
        ("选择题", 3, 8),
        ("选择题", 4, 4),
        ("填空题", 4, 3),
        ("简答题", 6, 3),
        ("综合题", 10, 2),
    ],
}


def seed_exam_detail():
    """为已有考试生成细目表和小题分数据"""
    db = SessionLocal()

    # Check existing data
    if db.query(ExamQuestion).first():
        print("Exam questions already seeded, cleaning and reseeding...")
        db.query(ScoreDetail).delete()
        db.query(ExamQuestion).delete()
        db.commit()

    # Get the exam
    exam = db.query(Exam).first()
    if not exam:
        print("No exam found, run seed.py first")
        db.close()
        return

    exam_subjects = db.query(ExamSubject).filter(ExamSubject.exam_id == exam.id).all()
    print(f"Found exam: {exam.name}, {len(exam_subjects)} subjects")

    # Get all students in this exam's grade
    from app.models.student import Student
    students = db.query(Student).filter(Student.class_id.in_(
        db.query(Student.class_id).filter(Student.id.in_(
            db.query(Score.student_id).filter(
                Score.exam_subject_id.in_([es.id for es in exam_subjects])
            )
        ))
    )).all()

    question_map = {}  # exam_subject_id -> list of questions

    for es in exam_subjects:
        subj = db.query(Subject).filter(Subject.id == es.subject_id).first()
        subj_name = subj.name if subj else "未知"
        config = SUBJECT_QUESTION_CONFIG.get(subj_name, [("选择题", 5, 6)])

        # Get knowledge points for this subject
        kps = db.query(SubjectKnowledgePoint).filter(
            SubjectKnowledgePoint.subject_id == es.subject_id
        ).all()
        kp_ids = [kp.id for kp in kps]

        # Skip subjects with no KP
        if not kp_ids:
            print(f"  Skipping {subj_name} (no KPs)")
            continue

        created_questions = []
        question_no = 1

        for qtype, score_per_q, q_count in config:
            for _ in range(q_count):
                if not kp_ids:
                    break
                kp_id = random.choice(kp_ids)
                difficulty = round(random.uniform(0.3, 0.95), 2)

                q = ExamQuestion(
                    exam_subject_id=es.id,
                    question_no=question_no,
                    question_type=qtype,
                    full_score=score_per_q,
                    knowledge_point_id=kp_id,
                    difficulty=difficulty,
                    estimated_pass_rate=round(difficulty * 100, 1),
                    cognitive_level=random.choice(["识记", "理解", "应用", "综合"]),
                )
                db.add(q)
                created_questions.append(q)
                question_no += 1

        db.flush()
        question_map[es.id] = created_questions
        print(f"  {subj_name}: {len(created_questions)} questions created")

    # Now create ScoreDetail records
    detail_count = 0
    for es in exam_subjects:
        questions = question_map.get(es.id, [])
        if not questions:
            continue

        scores = db.query(Score).filter(Score.exam_subject_id == es.id).all()
        for score in scores:
            total_q_score = sum(q.full_score for q in questions)
            if total_q_score <= 0:
                continue

            student_ability = score.score_value / es.full_score if es.full_score else 0.5
            remaining_earned = score.score_value

            for i, q in enumerate(questions):
                if i == len(questions) - 1:
                    # Last question gets the remainder
                    detail_score = max(0, min(q.full_score, remaining_earned))
                else:
                    # Expected score based on student ability and question difficulty
                    expected_pct = max(0.1, min(0.95, student_ability * (1 + (1 - q.difficulty or 0.5))))
                    expected = q.full_score * expected_pct
                    variance = random.uniform(-0.15, 0.15) * q.full_score
                    detail_score = max(0, min(q.full_score, expected + variance))
                    remaining_earned -= detail_score
                    remaining_earned = max(0, remaining_earned)

                detail_score = round(detail_score, 1)

                sd = ScoreDetail(
                    score_id=score.id,
                    question_id=q.id,
                    score_value=detail_score,
                )
                db.add(sd)
                detail_count += 1

        db.commit()

    db.close()
    print(f"\nTotal: {detail_count} score detail records created")
    print("Exam detail seed complete!")


if __name__ == "__main__":
    seed_exam_detail()

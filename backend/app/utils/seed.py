"""
\u6570\u636e\u5e93\u521d\u59cb\u5316\u548c\u6d4b\u8bd5\u6570\u636e\u586b\u5145\u811a\u672c
\u7528\u6cd5: python -m app.utils.seed
"""
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.school import Grade, ClassInfo
from app.models.student import Student
from app.models.subject import Subject
from app.models.exam import Exam, ExamSubject
from app.models.score import Score
import uuid
from datetime import date, datetime, timezone
import random


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if already seeded
    if db.query(User).first():
        print("Database already has data, skipping seed")
        db.close()
        return

    # Admin user
    admin = User(
        username="admin",
        password_hash=get_password_hash("Admin@ChangeMe2026"),
        display_name="\u7ba1\u7406\u5458",
        role="admin",
        is_active=True,\n        needs_password_change=True,
    )
    db.add(admin)

    # Grades
    g1 = Grade(name="\u9ad8\u4e00", sort_order=1)
    g2 = Grade(name="\u9ad8\u4e8c", sort_order=2)
    g3 = Grade(name="\u9ad8\u4e09", sort_order=3)
    db.add_all([g1, g2, g3])
    db.flush()

    # Classes
    classes = []
    for g in [g1, g2, g3]:
        for i in range(1, 5):
            c = ClassInfo(name=f"{g.name}({i})\u73ed", grade_id=g.id)
            db.add(c)
            classes.append(c)
    db.flush()

    # Subjects
    subjects_data = [
        ("\u8bed\u6587", 150, 1),
        ("\u6570\u5b66", 150, 2),
        ("\u82f1\u8bed", 150, 3),
        ("\u7269\u7406", 100, 4),
        ("\u5316\u5b66", 100, 5),
        ("\u751f\u7269", 100, 6),
    ]
    subjects = []
    for name, full_score, order in subjects_data:
        s = Subject(name=name, full_score=full_score, sort_order=order)
        db.add(s)
        subjects.append(s)
    db.flush()

    # Students (30 per class for g1)
    students = []
    for cls in classes[:4]:  # g1 classes
        for i in range(1, 31):
            gender = "\u7537" if i % 2 == 1 else "\u5973"
            st = Student(
                student_no=f"2026{str(classes.index(cls)+1).zfill(2)}{str(i).zfill(3)}",
                name=f"\u5b66\u751f{cls.name}_{i}",
                gender=gender,
                class_id=cls.id,
            )
            db.add(st)
            students.append(st)
    db.flush()

    # Exam
    exam = Exam(
        name="2026\u5e74\u7b2c\u4e00\u6b21\u6708\u8003",
        exam_date=date(2026, 3, 15),
        exam_type="\u6708\u8003",
        grade_id=g1.id,
    )
    db.add(exam)
    db.flush()

    # Exam subjects
    exam_subjects = []
    for subj in subjects:
        es = ExamSubject(
            exam_id=exam.id,
            subject_id=subj.id,
            full_score=subj.full_score,
            weight=1.0,
        )
        db.add(es)
        exam_subjects.append(es)
    db.flush()

    # Scores
    for student in students:
        for es in exam_subjects:
            # Simulate realistic scores
            mean = es.full_score * 0.65
            std = es.full_score * 0.12
            score_val = max(0, min(es.full_score, random.gauss(mean, std)))
            score = Score(
                student_id=student.id,
                exam_subject_id=es.id,
                score_value=round(score_val, 1),
                status="normal",
            )
            db.add(score)
    db.commit()
    db.close()
    print("Seed data created successfully!")
    print("  ⚠️ 首次登录请使用 admin / Admin@ChangeMe2026，系统将要求修改密码")
    print(f"  - 1 admin user (admin/Admin@ChangeMe2026) - 首次登录需修改密码")
    print(f"  - 3 grades, 12 classes")
    print(f"  - 6 subjects")
    print(f"  - 120 students")
    print(f"  - 1 exam with 720 score records")


if __name__ == "__main__":
    seed()

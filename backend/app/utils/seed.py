"""数据库初始化和测试数据填充脚本
用法: python -m app.utils.seed
"""
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.school import Grade, ClassInfo
from app.models.student import Student
from app.models.subject import Subject
from app.models.exam import Exam, ExamSubject
from app.models.score import Score
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
        display_name="管理员",
        role="admin",
        is_active=True,
        needs_password_change=True,
    )
    db.add(admin)

    # Grades
    g1 = Grade(name="高一", sort_order=1)
    g2 = Grade(name="高二", sort_order=2)
    g3 = Grade(name="高三", sort_order=3)
    db.add_all([g1, g2, g3])
    db.flush()

    # Classes
    classes = []
    for g in [g1, g2, g3]:
        for i in range(1, 5):
            c = ClassInfo(name=f"{g.name}({i})班", grade_id=g.id)
            db.add(c)
            classes.append(c)
    db.flush()

    # Subjects
    subjects_data = [
        ("语文", 150, 1),
        ("数学", 150, 2),
        ("英语", 150, 3),
        ("物理", 100, 4),
        ("化学", 100, 5),
        ("生物", 100, 6),
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
            gender = "男" if i % 2 == 1 else "女"
            st = Student(
                student_no=f"2026{str(classes.index(cls)+1).zfill(2)}{str(i).zfill(3)}",
                name=f"学生{cls.name}_{i}",
                gender=gender,
                class_id=cls.id,
            )
            db.add(st)
            students.append(st)
    db.flush()

    # Exam
    exam = Exam(
        name="2026年第一次月考",
        exam_date=date(2026, 3, 15),
        exam_type="月考",
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

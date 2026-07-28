
import sys, os, uuid, random
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.school import Grade, ClassInfo
from app.models.student import Student
from app.models.subject import Subject
from app.models.exam import Exam, ExamSubject
from app.models.score import Score

# Recreate all tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Admin
admin = User(username="admin", password_hash=get_password_hash("admin123"), display_name="管理员", role="admin", is_active=True)
db.add(admin)
# Teacher user
teacher = User(username="teacher", password_hash=get_password_hash("teacher123"), display_name="张老师", role="teacher", is_active=True)
db.add(teacher)

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
    ("语文", 150, 1), ("数学", 150, 2), ("英语", 150, 3),
    ("物理", 100, 4), ("化学", 100, 5), ("生物", 100, 6),
]
subjects = []
for name, fs, order in subjects_data:
    s = Subject(name=name, full_score=fs, sort_order=order)
    db.add(s)
    subjects.append(s)
db.flush()

# Students (120 for g1 classes, 60 each for g2/g3)
all_students = []
for cls in classes[:4]:
    for i in range(1, 31):
        gender = "男" if i % 2 == 1 else "女"
        st = Student(
            student_no=f"2026{str(classes.index(cls)+1).zfill(2)}{str(i).zfill(3)}",
            name=f"学生{cls.name}_{i}", gender=gender, class_id=cls.id
        )
        db.add(st)
        all_students.append(st)

for cls in classes[4:8]:
    for i in range(1, 31):
        st = Student(
            student_no=f"2025{str(classes.index(cls)+1).zfill(2)}{str(i).zfill(3)}",
            name=f"学生{cls.name}_{i}", gender="男" if i % 2 == 1 else "女", class_id=cls.id
        )
        db.add(st)
        all_students.append(st)

for cls in classes[8:12]:
    for i in range(1, 31):
        st = Student(
            student_no=f"2024{str(classes.index(cls)+1).zfill(2)}{str(i).zfill(3)}",
            name=f"学生{cls.name}_{i}", gender="男" if i % 2 == 1 else "女", class_id=cls.id
        )
        db.add(st)
        all_students.append(st)
db.flush()

# 5 exams for g1
exam_defs = [
    ("2026年3月月考", date(2026, 3, 15), "月考", g1.id, 0.60, 0.10),
    ("2026年4月月考", date(2026, 4, 18), "月考", g1.id, 0.63, 0.11),
    ("2026年期中考试", date(2026, 5, 10), "期中", g1.id, 0.65, 0.12),
    ("2026年5月月考", date(2026, 6, 5), "月考", g1.id, 0.68, 0.11),
    ("2026年期末考试", date(2026, 7, 2), "期末", g1.id, 0.70, 0.12),
]

g1_students = [s for s in all_students if s.class_id in [c.id for c in classes[:4]]]

for ename, edate, etype, gid, base_mean, base_std in exam_defs:
    exam = Exam(name=ename, exam_date=edate, exam_type=etype, grade_id=gid)
    db.add(exam)
    db.flush()

    for subj in subjects:
        es = ExamSubject(exam_id=exam.id, subject_id=subj.id, full_score=subj.full_score, weight=1.0)
        db.add(es)
    db.flush()

    exam_subjects = db.query(ExamSubject).filter(ExamSubject.exam_id == exam.id).all()

    for student in g1_students:
        for es in exam_subjects:
            subj = [s for s in subjects if s.id == es.subject_id][0]
            mean = es.full_score * base_mean
            std = es.full_score * base_std
            student_boost = hash(str(student.id) + str(es.id)) % 30 / 100 * es.full_score * 0.15
            score_val = max(0, min(es.full_score, random.gauss(mean + student_boost, std)))
            db.add(Score(student_id=student.id, exam_subject_id=es.id, score_value=round(score_val, 1), status="normal"))

# 3 exams for g2
exam_defs_g2 = [
    ("2026年3月月考", date(2026, 3, 16), "月考", g2.id, 0.62, 0.12),
    ("2026年期中考试", date(2026, 5, 12), "期中", g2.id, 0.64, 0.13),
    ("2026年6月月考", date(2026, 6, 20), "月考", g2.id, 0.66, 0.12),
]

g2_students = [s for s in all_students if s.class_id in [c.id for c in classes[4:8]]]

for ename, edate, etype, gid, base_mean, base_std in exam_defs_g2:
    exam = Exam(name=ename, exam_date=edate, exam_type=etype, grade_id=gid)
    db.add(exam)
    db.flush()
    for subj in subjects:
        db.add(ExamSubject(exam_id=exam.id, subject_id=subj.id, full_score=subj.full_score, weight=1.0))
    db.flush()
    exam_subjects = db.query(ExamSubject).filter(ExamSubject.exam_id == exam.id).all()
    for student in g2_students:
        for es in exam_subjects:
            subj = [s for s in subjects if s.id == es.subject_id][0]
            mean = es.full_score * base_mean
            std = es.full_score * base_std
            score_val = max(0, min(es.full_score, random.gauss(mean, std)))
            db.add(Score(student_id=student.id, exam_subject_id=es.id, score_value=round(score_val, 1), status="normal"))

db.commit()
db.close()

print("=== Seed data created ===")
print(f"Users: 2 (admin/admin123, teacher/teacher123)")
print(f"Grades: 3, Classes: 12, Subjects: 6")
print(f"Students: {len(all_students)}")
print(f"G1 Exams: {len(exam_defs)} (with trend: base_mean 0.60->0.70)")
print(f"G2 Exams: {len(exam_defs_g2)}")
print(f"Total score records: ~{(len(exam_defs)*6*120 + len(exam_defs_g2)*6*60)}")


"""Tests for core backend APIs: subjects, schools, and analysis."""
import pytest
from app.core.security import create_access_token

HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def _seed_test_data(db_session):
    """Seed minimal test data before each test."""
    from app.models.subject import Subject
    from app.models.school import Grade, ClassInfo
    from app.models.student import Student
    from app.models.exam import Exam, ExamSubject
    from app.models.score import Score
    from datetime import datetime, date
    import uuid

    # Grades
    g1 = Grade(id=uuid.uuid4(), name="测试一年级", sort_order=1)
    g2 = Grade(id=uuid.uuid4(), name="测试二年级", sort_order=2)
    db_session.add_all([g1, g2])

    # Classes
    c1 = ClassInfo(id=uuid.uuid4(), name="测试一班", grade_id=g1.id)
    c2 = ClassInfo(id=uuid.uuid4(), name="测试二班", grade_id=g1.id)
    db_session.add_all([c1, c2])

    # Subjects
    s1 = Subject(id=uuid.uuid4(), name="语文", full_score=150, sort_order=1)
    s2 = Subject(id=uuid.uuid4(), name="数学", full_score=150, sort_order=2)
    db_session.add_all([s1, s2])

    # Students
    stu1 = Student(id=uuid.uuid4(), student_no="T001", name="测试学生A", gender="男", class_id=c1.id)
    stu2 = Student(id=uuid.uuid4(), student_no="T002", name="测试学生B", gender="女", class_id=c1.id)
    db_session.add_all([stu1, stu2])

    # Exam
    exam = Exam(
        id=uuid.uuid4(),
        name="测试考试",
        exam_date=date(2026, 7, 1),
        exam_type="月考",
        grade_id=g1.id,
    )
    db_session.add(exam)

    # ExamSubjects
    es1 = ExamSubject(id=uuid.uuid4(), exam_id=exam.id, subject_id=s1.id, full_score=150, weight=1)
    es2 = ExamSubject(id=uuid.uuid4(), exam_id=exam.id, subject_id=s2.id, full_score=150, weight=1)
    db_session.add_all([es1, es2])

    # Scores
    sc1 = Score(id=uuid.uuid4(), student_id=stu1.id, exam_subject_id=es1.id, score_value=120.0, status="正常")
    sc2 = Score(id=uuid.uuid4(), student_id=stu1.id, exam_subject_id=es2.id, score_value=130.0, status="正常")
    sc3 = Score(id=uuid.uuid4(), student_id=stu2.id, exam_subject_id=es1.id, score_value=90.0, status="正常")
    sc4 = Score(id=uuid.uuid4(), student_id=stu2.id, exam_subject_id=es2.id, score_value=110.0, status="正常")
    db_session.add_all([sc1, sc2, sc3, sc4])

    db_session.commit()

    # Store IDs for use in tests
    return {
        "grade1_id": str(g1.id),
        "grade2_id": str(g2.id),
        "class1_id": str(c1.id),
        "class2_id": str(c2.id),
        "subject1_id": str(s1.id),
        "subject2_id": str(s2.id),
        "student1_id": str(stu1.id),
        "student2_id": str(stu2.id),
        "exam_id": str(exam.id),
        "exam_subject1_id": str(es1.id),
        "exam_subject2_id": str(es2.id),
    }


# ==================== Subjects API ====================

class TestSubjects:
    def test_list_subjects(self, client):
        resp = client.get("/api/v1/subjects/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        names = [s["name"] for s in data]
        assert "语文" in names
        assert "数学" in names

    def test_create_subject(self, client):
        resp = client.post("/api/v1/subjects/", json={"name": "英语", "full_score": 100, "sort_order": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "英语"
        assert data["full_score"] == 100
        assert "id" in data

    def test_create_duplicate_subject(self, client):
        resp = client.post("/api/v1/subjects/", json={"name": "语文", "full_score": 100})
        assert resp.status_code == 400

    def test_update_subject(self, client, _seed_test_data):
        sid = _seed_test_data["subject1_id"]
        resp = client.put(f"/api/v1/subjects/{sid}", json={"name": "语文改", "full_score": 160, "sort_order": 1})
        assert resp.status_code == 200
        assert resp.json()["name"] == "语文改"

    def test_delete_subject(self, client, _seed_test_data):
        sid = _seed_test_data["subject1_id"]
        resp = client.delete(f"/api/v1/subjects/{sid}")
        assert resp.status_code == 200
        # Verify deletion
        resp = client.get("/api/v1/subjects/")
        names = [s["name"] for s in resp.json()]
        assert "语文" not in names


# ==================== Schools API ====================

class TestSchools:
    def test_list_grades(self, client):
        resp = client.get("/api/v1/schools/grades")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        names = [g["name"] for g in data]
        assert "测试一年级" in names

    def test_create_grade(self, client):
        resp = client.post("/api/v1/schools/grades", json={"name": "测试三年级", "sort_order": 3})
        assert resp.status_code == 200
        assert resp.json()["name"] == "测试三年级"

    def test_update_grade(self, client, _seed_test_data):
        gid = _seed_test_data["grade1_id"]
        resp = client.put(f"/api/v1/schools/grades/{gid}", json={"name": "一年级改", "sort_order": 1})
        assert resp.status_code == 200
        assert resp.json()["name"] == "一年级改"

    def test_delete_grade(self, client, _seed_test_data):
        gid = _seed_test_data["grade2_id"]
        resp = client.delete(f"/api/v1/schools/grades/{gid}")
        assert resp.status_code == 200

    def test_list_classes(self, client):
        resp = client.get("/api/v1/schools/classes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        names = [c["name"] for c in data]
        assert "测试一班" in names

    def test_list_classes_filter_by_grade(self, client, _seed_test_data):
        gid = _seed_test_data["grade1_id"]
        resp = client.get(f"/api/v1/schools/classes?grade_id={gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_create_class(self, client, _seed_test_data):
        gid = _seed_test_data["grade1_id"]
        resp = client.post("/api/v1/schools/classes", json={"name": "测试三班", "grade_id": gid})
        assert resp.status_code == 200
        assert resp.json()["name"] == "测试三班"

    def test_create_class_invalid_grade(self, client):
        resp = client.post("/api/v1/schools/classes", json={"name": "无效班", "grade_id": "00000000-0000-0000-0000-000000000000"})
        assert resp.status_code == 404

    def test_update_class(self, client, _seed_test_data):
        cid = _seed_test_data["class1_id"]
        gid = _seed_test_data["grade1_id"]
        resp = client.put(f"/api/v1/schools/classes/{cid}", json={"name": "一班改", "grade_id": gid})
        assert resp.status_code == 200
        assert resp.json()["name"] == "一班改"

    def test_delete_class(self, client, _seed_test_data):
        cid = _seed_test_data["class2_id"]
        resp = client.delete(f"/api/v1/schools/classes/{cid}")
        assert resp.status_code == 200

    def test_class_info_includes_grade_name(self, client, _seed_test_data):
        cid = _seed_test_data["class1_id"]
        resp = client.get("/api/v1/schools/classes")
        data = resp.json()
        cls = next(c for c in data if c["id"] == cid)
        assert cls["grade_name"] is not None
        assert cls["student_count"] >= 0


# ==================== Analysis Dashboard API ====================

class TestAnalysis:
    def test_dashboard_returns_stats(self, client):
        resp = client.get("/api/v1/analysis/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "stats" in data
        s = data["stats"]
        assert s["grades"] >= 2
        assert s["classes"] >= 2
        assert s["subjects"] >= 2
        assert s["students"] >= 2
        assert s["exams"] >= 1
        assert s["scores"] >= 4

    def test_dashboard_has_recent_exams(self, client):
        resp = client.get("/api/v1/analysis/dashboard")
        data = resp.json()
        assert len(data["recent_exams"]) >= 1
        exam = data["recent_exams"][0]
        assert "exam_name" in exam
        assert "avg_rate" in exam
        assert "student_count" in exam

    def test_dashboard_subject_stats(self, client):
        resp = client.get("/api/v1/analysis/dashboard")
        data = resp.json()
        assert len(data["subject_stats"]) >= 2
        for ss in data["subject_stats"]:
            assert "subject_name" in ss
            assert "avg_score" in ss
            assert "max_score" in ss

    def test_dashboard_risk_students(self, client):
        resp = client.get("/api/v1/analysis/dashboard")
        data = resp.json()
        assert len(data["risk_students"]) >= 1
        for rs in data["risk_students"]:
            assert "student_name" in rs
            assert "avg_rate" in rs

    def test_dashboard_class_ranking(self, client):
        resp = client.get("/api/v1/analysis/dashboard")
        data = resp.json()
        assert len(data["class_ranking"]) >= 1
        for grade in data["class_ranking"]:
            assert "grade_name" in grade
            assert len(grade["classes"]) >= 1

    def test_dashboard_exam_type_stats(self, client):
        resp = client.get("/api/v1/analysis/dashboard")
        data = resp.json()
        stats = data["exam_type_stats"]
        assert "monthly" in stats
        assert stats["monthly"] >= 1

    def test_dashboard_trend(self, client):
        resp = client.get("/api/v1/analysis/dashboard")
        data = resp.json()
        assert "direction" in data["trend"]
        assert "description" in data["trend"]
        assert data["trend"]["direction"] in ("up", "down", "stable")

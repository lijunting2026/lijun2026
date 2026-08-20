"""Tests for scoring schemes, conversion, score lines, and dual-track analysis."""
import io
import uuid
from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.models.exam import Exam, ExamSubject
from app.models.school import Grade, ClassInfo
from app.models.score import Score
from app.models.scoring import ScoreLine, ScoringScheme
from app.models.student import Student
from app.models.subject import Subject
from app.services.analytics.analysis_service import AnalysisService
from app.services.analytics.score_conversion_service import ScoreConversionService


@pytest.fixture
def scoring_db(db_session: Session):
    """Exam with one raw subject (Chinese) and one converted subject (Physics)."""
    g = Grade(name="G-SCORE", sort_order=1)
    db_session.add(g)
    db_session.flush()
    c1 = ClassInfo(name="C-SCORE", grade_id=g.id)
    db_session.add(c1)
    db_session.flush()
    s_raw = Subject(name="Chinese", full_score=150, sort_order=1)
    s_conv = Subject(name="Physics", full_score=100, sort_order=2)
    db_session.add_all([s_raw, s_conv])
    db_session.flush()
    scheme = ScoringScheme(
        name="Test Scheme",
        brackets=[
            {"rank_start": 0.0, "rank_end": 0.3, "score_start": 100, "score_end": 85},
            {"rank_start": 0.3, "rank_end": 1.0, "score_start": 84, "score_end": 40},
        ],
        is_preset=False,
    )
    db_session.add(scheme)
    db_session.flush()
    exam = Exam(name="Mock Exam", exam_date=date(2026, 8, 20), exam_type="sim", grade_id=g.id)
    db_session.add(exam)
    db_session.flush()
    es_raw = ExamSubject(
        exam_id=exam.id, subject_id=s_raw.id, full_score=150, weight=1,
        scoring_type="raw",
    )
    es_conv = ExamSubject(
        exam_id=exam.id, subject_id=s_conv.id, full_score=100, weight=1,
        scoring_type="converted", scheme_id=scheme.id, conversion_mode="auto",
    )
    db_session.add_all([es_raw, es_conv])
    db_session.flush()
    students = []
    for i in range(10):
        st = Student(student_no=f"SC{i:02d}", name=f"Stu{i}", gender="M", class_id=c1.id)
        db_session.add(st)
        students.append(st)
    db_session.flush()
    # Chinese raw: 60,70,...150 ; Physics raw: 30,37,...93
    for i, st in enumerate(students):
        db_session.add(Score(student_id=st.id, exam_subject_id=es_raw.id, score_value=60.0 + i * 10, class_id=c1.id))
        db_session.add(Score(student_id=st.id, exam_subject_id=es_conv.id, score_value=30.0 + i * 7, class_id=c1.id))
    db_session.commit()
    return {
        "exam_id": str(exam.id),
        "exam_subject_raw_id": str(es_raw.id),
        "exam_subject_conv_id": str(es_conv.id),
        "scheme_id": str(scheme.id),
        "subject_conv_id": str(s_conv.id),
        "subject_raw_id": str(s_raw.id),
        "grade_id": str(g.id),
        "class_id": str(c1.id),
    }


def test_conversion_service_maps_percentiles(scoring_db, db_session: Session):
    service = ScoreConversionService(db_session)
    result = service.convert_exam_subject(uuid.UUID(scoring_db["exam_subject_conv_id"]))
    assert result["converted"] == 10
    rows = db_session.query(Score).filter(Score.exam_subject_id == uuid.UUID(scoring_db["exam_subject_conv_id"])).all()
    by_raw = {s.score_value: s.converted_score for s in rows}
    # bracket0 single score -> takes segment upper bound
    assert by_raw[93.0] == 100.0
    assert by_raw[86.0] == 85.0
    # bracket1 linear interpolation: 30->40, 79->84
    assert by_raw[30.0] == 40.0
    assert by_raw[79.0] == 84.0
    assert all(s.converted_source == "system" for s in rows)


def test_manual_mode_does_not_overwrite(scoring_db, db_session: Session):
    es = db_session.query(ExamSubject).filter(ExamSubject.id == uuid.UUID(scoring_db["exam_subject_conv_id"])).first()
    es.conversion_mode = "manual"
    db_session.commit()
    row = db_session.query(Score).filter(Score.exam_subject_id == es.id).first()
    row.converted_score = 77.0
    row.converted_source = "official"
    db_session.commit()
    service = ScoreConversionService(db_session)
    service.convert_exam_subject(es.id)
    db_session.refresh(row)
    assert row.converted_score == 77.0
    assert row.converted_source == "official"


def test_scoring_scheme_api(client, db_session: Session):
    preset = ScoringScheme(
        name="Preset", is_preset=True,
        brackets=[{"rank_start": 0, "rank_end": 1, "score_start": 100, "score_end": 40}],
    )
    db_session.add(preset)
    db_session.commit()
    r = client.get("/api/v1/scoring-schemes/")
    assert r.status_code == 200
    presets = [s for s in r.json() if s["is_preset"]]
    assert len(presets) >= 1
    r = client.delete(f"/api/v1/scoring-schemes/{presets[0]['id']}")
    assert r.status_code == 400
    r = client.post("/api/v1/scoring-schemes/", json={
        "name": "Custom", "description": "d",
        "brackets": [{"rank_start": 0, "rank_end": 1, "score_start": 100, "score_end": 40}],
    })
    assert r.status_code == 200
    assert r.json()["is_preset"] is False


def test_score_lines_crud_and_import(scoring_db, client):
    exam_id = scoring_db["exam_id"]
    r = client.post(f"/api/v1/exams/{exam_id}/score-lines", json=[
        {"line_name": "Undergrad", "line_type": "total", "score_value": 400},
        {"line_name": "PhysicsLine", "line_type": "subject", "subject_id": scoring_db["subject_conv_id"], "score_value": 60},
    ])
    assert r.status_code == 200
    lines = client.get(f"/api/v1/exams/{exam_id}/score-lines").json()
    assert len(lines) == 2

    # batch import via excel
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["线名", "类型", "科目", "分数", "来源"])
    ws.append(["SpecialLine", "总分", "", 420, "official"])
    ws.append(["PhysicsLine", "单科", "Physics", 65, "official"])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    r = client.post(
        f"/api/v1/exams/{exam_id}/score-lines/import",
        files={"file": ("lines.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r.status_code == 200
    assert r.json()["message"].startswith("成功导入 2")
    lines = client.get(f"/api/v1/exams/{exam_id}/score-lines").json()
    names = {(l["line_name"], l["line_type"]) for l in lines}
    assert ("SpecialLine", "total") in names
    assert ("PhysicsLine", "subject") in names


def test_scoring_config_api(scoring_db, client):
    r = client.put(f"/api/v1/exams/{scoring_db['exam_id']}/scoring-config", json={
        "subjects": [
            {"exam_subject_id": scoring_db["exam_subject_conv_id"], "scoring_type": "converted",
             "scheme_id": scoring_db["scheme_id"], "conversion_mode": "manual"},
        ]
    })
    assert r.status_code == 200
    cfg = client.get(f"/api/v1/exams/{scoring_db['exam_id']}/scoring-config").json()
    conv = [c for c in cfg if c["exam_subject_id"] == scoring_db["exam_subject_conv_id"]][0]
    assert conv["scoring_type"] == "converted"
    assert conv["conversion_mode"] == "manual"


def test_convert_endpoint_and_dual_analysis(scoring_db, client):
    exam_id = scoring_db["exam_id"]
    r = client.post(f"/api/v1/scores/{scoring_db['exam_subject_conv_id']}/convert")
    assert r.status_code == 200
    assert r.json()["converted"] == 10

    # line stats: total = chinese raw + physics converted
    client.post(f"/api/v1/exams/{exam_id}/score-lines", json=[
        {"line_name": "LineA", "line_type": "total", "score_value": 400},
        {"line_name": "LineB", "line_type": "total", "score_value": 100},
        {"line_name": "PLine", "line_type": "subject", "subject_id": scoring_db["subject_conv_id"], "score_value": 60},
    ])
    stats = client.get(f"/api/v1/analysis/exam/{exam_id}/line-stats?score_mode=converted").json()
    assert stats["total_students"] == 10
    line_b = [l for l in stats["total_lines"] if l["line_name"] == "LineB"][0]
    assert line_b["count"] == 10  # everyone's total >= 100
    line_a = [l for l in stats["total_lines"] if l["line_name"] == "LineA"][0]
    assert line_a["count"] == 0  # max total = 150 + 100 = 250 < 400
    pl = [l for l in stats["subject_lines"] if l["line_name"] == "PLine"][0]
    # converted >= 60: 65,71,78,84,85,100 -> 6 students
    assert pl["count"] == 6
    assert len(stats["dual_lines"]) == 2

    # one-point table
    table = client.get(f"/api/v1/analysis/exam/{exam_id}/one-point-table?score_mode=converted").json()
    assert table["total_students"] == 10
    assert sum(item["count"] for item in table["items"]) == 10
    assert table["items"][-1]["cumulative"] == 10  # 最低分处累计等于总人数

    # exam analysis with converted mode
    analysis = client.get(f"/api/v1/analysis/exam/{exam_id}?score_mode=converted").json()
    assert analysis["score_mode"] == "converted"
    phy = [s for s in analysis["grade_stats"] if s["subject_name"] == "Physics"][0]
    assert phy["avg_score"] > 60

    # auto mode degrades to raw when no converted scores exist (fresh exam)
    analysis_raw = client.get(f"/api/v1/analysis/exam/{exam_id}?score_mode=auto").json()
    assert analysis_raw["score_mode"] == "converted"  # conversion already ran

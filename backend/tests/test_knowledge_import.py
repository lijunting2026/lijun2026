# -*- coding: utf-8 -*-
"""Tests for knowledge point smart import (excel/text/ai preview + merge commit)."""
import io
import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.exam_detail import KnowledgeSource, SubjectKnowledgePoint
from app.models.subject import Subject
from app.services.analytics.knowledge_import_service import (
    build_preview,
    commit_import,
    parse_excel,
    parse_text,
)


def _subject(db: Session) -> Subject:
    subj = Subject(name="Math-Import", full_score=150, sort_order=1)
    db.add(subj)
    db.commit()
    return subj


def test_parse_text_hierarchy():
    text = """第一章 集合
一、集合的含义与表示
1. 集合的概念
（1）元素的特性
（2）元素与集合的关系
二、集合间的基本关系
1. 子集
（1）子集的概念
Unit 1 函数
1.1 函数的概念"""
    roots = parse_text(text)
    names = [r["name"] for r in roots]
    assert names == ["第一章 集合", "Unit 1 函数"]
    ch1 = roots[0]
    assert [c["name"] for c in ch1["children"]] == ["一、集合的含义与表示", "二、集合间的基本关系"]
    inner = ch1["children"][0]["children"][0]
    assert inner["name"] == "1. 集合的概念"
    assert [c["name"] for c in inner["children"]] == ["（1）元素的特性", "（2）元素与集合的关系"]


def test_parse_excel_columns():
    wb_bytes = _make_excel_bytes()
    roots = parse_excel(wb_bytes)
    assert len(roots) == 1
    assert roots[0]["name"] == "高中"
    chapter = roots[0]["children"][0]["children"][0]  # 必修一 -> 第一章 集合
    assert chapter["name"] == "第一章 集合"
    unit1 = chapter["children"][0]
    assert unit1["name"] == "1.1 集合的概念"
    assert [c["name"] for c in unit1["children"]] == ["集合中元素的特性", "元素与集合的关系"]
    unit2 = chapter["children"][1]
    assert unit2["name"] == "1.2 集合间的基本关系"
    assert [c["name"] for c in unit2["children"]] == ["子集与真子集"]


def test_commit_import_and_merge(db_session: Session):
    subj = _subject(db_session)
    items = parse_text("第一章 集合\n1. 集合的概念\n2. 集合间的关系")
    r1 = commit_import(db_session, subj.id, "test-source", "curriculum", "rules", items)
    assert r1["created"] == 3
    assert r1["merged"] == 0

    # 同名再次导入 -> 合并，不新增
    items2 = parse_text("第一章 集合\n1. 集合的概念\n3. 集合的运算")
    r2 = commit_import(db_session, subj.id, "test-source-2", "curriculum", "rules", items2)
    assert r2["created"] == 1  # 仅 3. 集合的运算 新增
    assert r2["merged"] == 2

    total = db_session.query(SubjectKnowledgePoint).filter(
        SubjectKnowledgePoint.subject_id == subj.id
    ).count()
    assert total == 4
    sources = db_session.query(KnowledgeSource).all()
    assert len(sources) == 2


def test_preview_flags_duplicates(db_session: Session):
    subj = _subject(db_session)
    items = parse_text("第一章 集合\n1. 集合的概念")
    commit_import(db_session, subj.id, "s1", "curriculum", "rules", items)
    preview = build_preview(db_session, subj.id, items)
    assert preview["exists_count"] == 2
    assert all(i["exists"] for i in preview["items"])


def test_import_api_flow(client, db_session: Session):
    subj = _subject(db_session)
    sid = str(subj.id)
    r = client.get("/api/v1/knowledge-points/import/template.xlsx")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")

    r = client.post("/api/v1/knowledge-points/import/text", json={
        "subject_id": sid,
        "source_name": "课标文本",
        "text": "第一章 集合\n1. 集合的概念\n（1）元素的特性",
    })
    assert r.status_code == 200
    preview = r.json()
    assert preview["item_count"] == 3

    r = client.post("/api/v1/knowledge-points/import/preview", json={
        "subject_id": sid,
        "source_name": "课标文本",
        "import_mode": "rules",
        "items": preview["items"],
    })
    assert r.status_code == 200
    assert r.json()["created"] == 3

    # 静态路由 /sources 不被 /{subject_id} 抢占
    r = client.get("/api/v1/knowledge-points/sources")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # 树查询正常
    r = client.get(f"/api/v1/knowledge-points/tree/{sid}")
    assert r.status_code == 200
    assert len(r.json()) == 1


def _make_excel_bytes() -> bytes:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["学段", "册次", "单元", "课", "节", "知识点"])
    ws.append(["高中", "必修一", "第一章 集合", "1.1 集合的概念", "", "集合中元素的特性"])
    ws.append(["", "", "", "", "", "元素与集合的关系"])
    ws.append(["", "", "", "1.2 集合间的基本关系", "", "子集与真子集"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

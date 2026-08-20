"""add scoring schemes, score lines, knowledge sources

Revision ID: 005_add_scoring_and_knowledge_source
Revises: 004_add_knowledge_and_questions
Create Date: 2026-08-20
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.types import Uuid

revision: str = "005_add_scoring_and_knowledge_source"
down_revision: Union[str, None] = "004_add_knowledge_and_questions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 赋分方案
    op.create_table(
        "scoring_schemes",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("brackets", sa.JSON(), nullable=False),
        sa.Column("is_preset", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Float(), server_default="0"),
    )

    # 2. 分数线
    op.create_table(
        "score_lines",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exam_id", Uuid(as_uuid=True), sa.ForeignKey("exams.id"), nullable=False),
        sa.Column("line_name", sa.String(50), nullable=False),
        sa.Column("line_type", sa.String(20), server_default="total"),
        sa.Column("subject_id", Uuid(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=True),
        sa.Column("score_value", sa.Float(), nullable=False),
        sa.Column("source", sa.String(20), server_default="official"),
    )

    # 3. 知识点导入来源
    op.create_table(
        "knowledge_sources",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subject_id", Uuid(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("source_name", sa.String(200), nullable=False),
        sa.Column("source_type", sa.String(20), server_default="textbook"),
        sa.Column("import_mode", sa.String(10), server_default="rules"),
        sa.Column("status", sa.String(20), server_default="preview"),
        sa.Column("file_hash", sa.String(64), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
    )

    # 4. exam_subjects 加列
    with op.batch_alter_table("exam_subjects") as batch_op:
        batch_op.add_column(sa.Column("scoring_type", sa.String(20), nullable=False, server_default="raw"))
        batch_op.add_column(sa.Column("scheme_id", Uuid(as_uuid=True), sa.ForeignKey("scoring_schemes.id", name="fk_exam_subjects_scheme_id"), nullable=True))
        batch_op.add_column(sa.Column("conversion_mode", sa.String(20), nullable=False, server_default="auto"))

    # 5. scores 加列
    with op.batch_alter_table("scores") as batch_op:
        batch_op.add_column(sa.Column("converted_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("converted_source", sa.String(20), nullable=False, server_default="official"))

    # 6. subject_knowledge_points 加列
    with op.batch_alter_table("subject_knowledge_points") as batch_op:
        batch_op.add_column(sa.Column("source_id", Uuid(as_uuid=True), sa.ForeignKey("knowledge_sources.id", name="fk_knowledge_points_source_id"), nullable=True))
        batch_op.add_column(sa.Column("origin", sa.String(20), nullable=False, server_default="custom"))


def downgrade() -> None:
    with op.batch_alter_table("subject_knowledge_points") as batch_op:
        batch_op.drop_column("origin")
        batch_op.drop_column("source_id")
    with op.batch_alter_table("scores") as batch_op:
        batch_op.drop_column("converted_source")
        batch_op.drop_column("converted_score")
    with op.batch_alter_table("exam_subjects") as batch_op:
        batch_op.drop_column("conversion_mode")
        batch_op.drop_column("scheme_id")
        batch_op.drop_column("scoring_type")
    op.drop_table("knowledge_sources")
    op.drop_table("score_lines")
    op.drop_table("scoring_schemes")

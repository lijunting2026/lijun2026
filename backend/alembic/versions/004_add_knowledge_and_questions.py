"""add knowledge points, exam questions, score details

Revision ID: 004_add_knowledge_and_questions
Revises: 003_add_chat_messages
Create Date: 2026-07-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.types import Uuid

revision: str = "004_add_knowledge_and_questions"
down_revision: Union[str, None] = "003_add_chat_messages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add columns to exam_subjects
    op.add_column("exam_subjects", sa.Column("difficulty", sa.Float(), nullable=True))
    op.add_column("exam_subjects", sa.Column("discrimination", sa.Float(), nullable=True))
    op.add_column("exam_subjects", sa.Column("reliability", sa.Float(), nullable=True))

    # 2. Create subject_knowledge_points table
    op.create_table(
        "subject_knowledge_points",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subject_id", Uuid(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("parent_id", Uuid(as_uuid=True), sa.ForeignKey("subject_knowledge_points.id"), nullable=True),
        sa.Column("sort_order", sa.Integer(), default=0),
        sa.Column("description", sa.Text(), default=""),
        sa.UniqueConstraint("subject_id", "name", name="uq_knowledge_point"),
    )

    # 3. Create exam_questions table
    op.create_table(
        "exam_questions",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exam_subject_id", Uuid(as_uuid=True), sa.ForeignKey("exam_subjects.id"), nullable=False),
        sa.Column("question_no", sa.Integer(), nullable=False),
        sa.Column("question_type", sa.String(50), default=""),
        sa.Column("full_score", sa.Float(), nullable=False),
        sa.Column("knowledge_point_id", Uuid(as_uuid=True), sa.ForeignKey("subject_knowledge_points.id"), nullable=True),
        sa.Column("difficulty", sa.Float(), nullable=True),
        sa.Column("cognitive_level", sa.String(50), default=""),
        sa.Column("estimated_pass_rate", sa.Float(), nullable=True),
        sa.Column("content", sa.Text(), default=""),
        sa.UniqueConstraint("exam_subject_id", "question_no", name="uq_exam_question_no"),
    )

    # 4. Create score_details table
    op.create_table(
        "score_details",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score_id", Uuid(as_uuid=True), sa.ForeignKey("scores.id"), nullable=False),
        sa.Column("question_id", Uuid(as_uuid=True), sa.ForeignKey("exam_questions.id"), nullable=False),
        sa.Column("score_value", sa.Float(), nullable=False, default=0),
    )


def downgrade() -> None:
    op.drop_table("score_details")
    op.drop_table("exam_questions")
    op.drop_table("subject_knowledge_points")
    op.drop_column("exam_subjects", "reliability")
    op.drop_column("exam_subjects", "discrimination")
    op.drop_column("exam_subjects", "difficulty")

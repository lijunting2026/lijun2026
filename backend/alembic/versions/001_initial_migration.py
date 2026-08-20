"""initial_migration

Revision ID: 001
Revises: 
Create Date: 2026-07-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.types import Uuid

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="admin"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Grades
    op.create_table(
        "grades",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Classes
    op.create_table(
        "classes",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("grade_id", Uuid(as_uuid=True), sa.ForeignKey("grades.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Subjects
    op.create_table(
        "subjects",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("full_score", sa.Float(), nullable=False, server_default="100"),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Students
    op.create_table(
        "students",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("student_no", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("gender", sa.String(10), server_default="未知"),
        sa.Column("class_id", Uuid(as_uuid=True), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Exams
    op.create_table(
        "exams",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("exam_type", sa.String(50), server_default="月考"),
        sa.Column("grade_id", Uuid(as_uuid=True), sa.ForeignKey("grades.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ExamSubjects
    op.create_table(
        "exam_subjects",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("exam_id", Uuid(as_uuid=True), sa.ForeignKey("exams.id"), nullable=False),
        sa.Column("subject_id", Uuid(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("full_score", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Scores
    op.create_table(
        "scores",
        sa.Column("id", Uuid(as_uuid=True), primary_key=True),
        sa.Column("student_id", Uuid(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("exam_subject_id", Uuid(as_uuid=True), sa.ForeignKey("exam_subjects.id"), nullable=False),
        sa.Column("score_value", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), server_default="normal"),
        sa.Column("class_id", Uuid(as_uuid=True), sa.ForeignKey("classes.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index("idx_scores_student_id", "scores", ["student_id"])
    op.create_index("idx_scores_exam_subject_id", "scores", ["exam_subject_id"])
    op.create_index("idx_scores_class_id", "scores", ["class_id"])
    op.create_index("idx_scores_student_exam", "scores", ["student_id", "exam_subject_id"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_scores_student_exam", table_name="scores")
    op.drop_index("idx_scores_class_id", table_name="scores")
    op.drop_index("idx_scores_exam_subject_id", table_name="scores")
    op.drop_index("idx_scores_student_id", table_name="scores")
    op.drop_table("scores")
    op.drop_table("exam_subjects")
    op.drop_table("exams")
    op.drop_table("students")
    op.drop_table("subjects")
    op.drop_table("classes")
    op.drop_table("grades")
    op.drop_table("users")

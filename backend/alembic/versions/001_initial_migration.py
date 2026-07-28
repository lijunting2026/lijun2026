"""initial_migration

Revision ID: 001
Revises: 
Create Date: 2026-07-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
# UUIDs are stored as strings for cross-database compatibility

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), default="editor"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Grades
    op.create_table(
        "grades",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("sort_order", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Classes
    op.create_table(
        "classes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("grade_id", sa.String(36), sa.ForeignKey("grades.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Subjects
    op.create_table(
        "subjects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("full_score", sa.Float, default=100),
        sa.Column("sort_order", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Students
    op.create_table(
        "students",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("student_no", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("gender", sa.String(10), default="未知"),
        sa.Column("class_id", sa.String(36), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Exams
    op.create_table(
        "exams",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("exam_date", sa.Date, nullable=False),
        sa.Column("exam_type", sa.String(50), default="月考"),
        sa.Column("grade_id", sa.String(36), sa.ForeignKey("grades.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ExamSubjects
    op.create_table(
        "exam_subjects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("exam_id", sa.String(36), sa.ForeignKey("exams.id"), nullable=False),
        sa.Column("subject_id", sa.String(36), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("full_score", sa.Float, nullable=False),
        sa.Column("weight", sa.Float, default=1.0),
    )

    # Scores
    op.create_table(
        "scores",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("student_id", sa.String(36), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("exam_subject_id", sa.String(36), sa.ForeignKey("exam_subjects.id"), nullable=False),
        sa.Column("score_value", sa.Float, nullable=False),
        sa.Column("status", sa.String(20), default="normal"),
        sa.Column("class_id", sa.String(36), sa.ForeignKey("classes.id"), nullable=True),
    )

    # Indexes
    op.create_index("idx_scores_student_id", "scores", ["student_id"])
    op.create_index("idx_scores_exam_subject_id", "scores", ["exam_subject_id"])
    op.create_index("idx_scores_class_id", "scores", ["class_id"])
    op.create_index("idx_scores_student_exam", "scores", ["student_id", "exam_subject_id"], unique=True)


def downgrade() -> None:
    op.drop_table("scores")
    op.drop_table("exam_subjects")
    op.drop_table("exams")
    op.drop_table("students")
    op.drop_table("subjects")
    op.drop_table("classes")
    op.drop_table("grades")
    op.drop_table("users")
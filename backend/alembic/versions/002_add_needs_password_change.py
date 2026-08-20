"""add needs_password_change column to users"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002_add_needs_password_change'
down_revision: Union[str, None] = '001_initial_migration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("needs_password_change", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    op.drop_column("users", "needs_password_change")
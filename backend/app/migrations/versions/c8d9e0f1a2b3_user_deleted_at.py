"""user deleted_at: удаление аккаунта с обезличиванием

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
"""

import sqlalchemy as sa
from alembic import op

revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "deleted_at")

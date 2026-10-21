"""target_funds.image: необязательное фото сбора (ключ в хранилище, как у чеков)

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
"""

import sqlalchemy as sa
from alembic import op

revision = "e0f1a2b3c4d5"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("target_funds", sa.Column("image", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("target_funds", "image")

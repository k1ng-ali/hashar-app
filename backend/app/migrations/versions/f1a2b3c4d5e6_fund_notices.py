"""fund_notices: уведомления совету фонда от платформы; fund_members.notices_read_at

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "f1a2b3c4d5e6"
down_revision = "e0f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fund_notices",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=True),
        sa.Column("dedupe_key", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_key", name="uq_fund_notices_dedupe_key"),
    )
    op.create_index("ix_fund_notices_fund_id", "fund_notices", ["fund_id"])
    op.create_index("ix_fund_notices_created_at", "fund_notices", ["created_at"])
    op.add_column("fund_members", sa.Column("notices_read_at", sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("fund_members", "notices_read_at")
    op.drop_index("ix_fund_notices_created_at", table_name="fund_notices")
    op.drop_index("ix_fund_notices_fund_id", table_name="fund_notices")
    op.drop_table("fund_notices")

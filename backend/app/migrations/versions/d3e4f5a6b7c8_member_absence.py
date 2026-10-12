"""member left/blocked dates and accrual pauses

- fund_members: left_at, blocked_at (статус left — вышел, запись не удаляется)
- member_accrual_pauses: месяцы, за которые совет решил не начислять взнос

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
"""

import sqlalchemy as sa
from alembic import op

revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fund_members", sa.Column("left_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("fund_members", sa.Column("blocked_at", sa.TIMESTAMP(timezone=True), nullable=True))
    # Дата блокировки раньше не хранилась — считаем, что блокировка началась сейчас
    op.execute("UPDATE fund_members SET blocked_at = now() WHERE status = 'blocked'")

    op.create_table(
        "member_accrual_pauses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("member_id", sa.BigInteger(), nullable=False),
        sa.Column("from_period", sa.String(length=7), nullable=False),
        sa.Column("to_period", sa.String(length=7), nullable=False),
        sa.Column("reason", sa.String(length=20), nullable=False),
        sa.Column("decided_by_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["fund_members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_member_accrual_pauses_fund_id"), "member_accrual_pauses", ["fund_id"], unique=False)
    op.create_index(op.f("ix_member_accrual_pauses_member_id"), "member_accrual_pauses", ["member_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_member_accrual_pauses_member_id"), table_name="member_accrual_pauses")
    op.drop_index(op.f("ix_member_accrual_pauses_fund_id"), table_name="member_accrual_pauses")
    op.drop_table("member_accrual_pauses")
    # Вышедших раньше удаляли — без статуса left их записи не нужны
    op.execute("DELETE FROM fund_members WHERE status = 'left'")
    op.drop_column("fund_members", "blocked_at")
    op.drop_column("fund_members", "left_at")

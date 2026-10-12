"""rate history, credited amounts on contributions, plan request contact

- funds.monthly_rate → fund_rates (тариф по месяцам)
- contributions: requisite_label, credited_amount, credited_currency
- plan_requests: contact

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
"""

import sqlalchemy as sa
from alembic import op

revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── История тарифа ───────────────────────────────────────────────────────
    op.create_table(
        "fund_rates",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fund_id", "period", name="uq_fund_rates_fund_id_period"),
    )
    op.create_index(op.f("ix_fund_rates_fund_id"), "fund_rates", ["fund_id"], unique=False)
    # Текущий тариф становится единственной записью с начала расчётов фонда
    op.execute("INSERT INTO fund_rates (fund_id, period, amount) SELECT id, start_period, monthly_rate FROM funds")
    op.drop_column("funds", "monthly_rate")

    # ─── Взносы ───────────────────────────────────────────────────────────────
    op.add_column("contributions", sa.Column("requisite_label", sa.String(length=255), nullable=True))
    op.add_column("contributions", sa.Column("credited_amount", sa.Integer(), nullable=True))
    op.add_column("contributions", sa.Column("credited_currency", sa.String(length=3), nullable=True))
    op.execute("UPDATE contributions SET credited_amount = amount, credited_currency = currency")
    op.execute("""
        UPDATE contributions c
        SET requisite_label = r.bank_name || ' · ' || r.card_or_account_number || ' · ' || r.recipient_name
        FROM payment_requisites r
        WHERE r.id = c.requisite_id
        """)
    op.alter_column("contributions", "credited_amount", nullable=False)
    op.alter_column("contributions", "credited_currency", nullable=False)
    op.create_index(op.f("ix_contributions_requisite_id"), "contributions", ["requisite_id"], unique=False)

    # ─── Заявки на тариф ──────────────────────────────────────────────────────
    op.add_column("plan_requests", sa.Column("contact", sa.String(length=150), server_default="", nullable=False))
    op.alter_column("plan_requests", "contact", server_default=None)


def downgrade() -> None:
    op.drop_column("plan_requests", "contact")

    op.drop_index(op.f("ix_contributions_requisite_id"), table_name="contributions")
    op.drop_column("contributions", "credited_currency")
    op.drop_column("contributions", "credited_amount")
    op.drop_column("contributions", "requisite_label")

    op.add_column("funds", sa.Column("monthly_rate", sa.Integer(), server_default="0", nullable=False))
    # Возвращаем последний действующий тариф
    op.execute("""
        UPDATE funds f
        SET monthly_rate = r.amount
        FROM (
            SELECT DISTINCT ON (fund_id) fund_id, amount FROM fund_rates ORDER BY fund_id, period DESC
        ) r
        WHERE r.fund_id = f.id
        """)
    op.drop_index(op.f("ix_fund_rates_fund_id"), table_name="fund_rates")
    op.drop_table("fund_rates")

"""production hardening: auth sessions, audit log, soft-deleted expenses, integrity constraints

- auth_sessions: refresh-токен указывает на сессию — выход её отзывает
- audit_events: журнал действий совета и админа платформы
- expenses.deleted_at / deleted_by_id: расход отменяется, а не удаляется
- CHECK-ограничения на суммы, валюты, статусы и роли — целостность держит сама БД
- один председатель на фонд и одна ожидающая заявка на тариф — частичные уникальные индексы

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a6b7c8d9e0f1"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None

CURRENCIES = "('tjs', 'rub', 'usd')"
PERIOD = r"'^\d{4}-(0[1-9]|1[0-2])$'"

# (таблица, имя, условие)
CHECKS = [
    # Фонды и счета
    ("funds", "ck_funds_base_currency", f"base_currency IN {CURRENCIES}"),
    ("funds", "ck_funds_plan", "plan IN ('free', 'pro', 'max', 'individual')"),
    ("funds", "ck_funds_start_period", f"start_period ~ {PERIOD}"),
    ("funds", "ck_funds_member_limit", "member_limit IS NULL OR member_limit > 0"),
    ("fund_accounts", "ck_fund_accounts_currency", f"currency IN {CURRENCIES}"),
    ("fund_rates", "ck_fund_rates_amount", "amount >= 0"),
    ("fund_rates", "ck_fund_rates_period", f"period ~ {PERIOD}"),
    # Участники
    ("fund_members", "ck_fund_members_role", "role IN ('resident', 'admin', 'chairman')"),
    ("fund_members", "ck_fund_members_status", "status IN ('pending', 'active', 'rejected', 'blocked', 'left')"),
    ("member_accrual_pauses", "ck_member_accrual_pauses_range", "from_period <= to_period"),
    ("member_accrual_pauses", "ck_member_accrual_pauses_reason", "reason IN ('left', 'blocked')"),
    # Взносы
    ("contributions", "ck_contributions_amount", "amount > 0"),
    ("contributions", "ck_contributions_credited_amount", "credited_amount > 0"),
    ("contributions", "ck_contributions_currency", f"currency IN {CURRENCIES}"),
    ("contributions", "ck_contributions_credited_currency", f"credited_currency IN {CURRENCIES}"),
    ("contributions", "ck_contributions_category", "category IN ('monthly_fee', 'target_fund')"),
    ("contributions", "ck_contributions_status", "status IN ('pending', 'approved', 'rejected')"),
    ("contributions", "ck_contributions_monthly_fee_target", "category = 'target_fund' OR target_fund_id IS NULL"),
    ("contributions", "ck_contributions_billing_period", f"billing_period IS NULL OR billing_period ~ {PERIOD}"),
    # Расходы, сборы, переводы
    ("expenses", "ck_expenses_amount", "amount > 0"),
    ("expenses", "ck_expenses_currency", f"currency IN {CURRENCIES}"),
    (
        "expenses",
        "ck_expenses_category",
        "category IN ('repair', 'electrical', 'emergency', 'household', 'landscaping', 'cctv')",
    ),
    ("target_funds", "ck_target_funds_target_amount", "target_amount > 0"),
    ("target_funds", "ck_target_funds_currency", f"currency IN {CURRENCIES}"),
    ("account_transfers", "ck_account_transfers_from_amount", "from_amount IS NULL OR from_amount > 0"),
    ("account_transfers", "ck_account_transfers_to_amount", "to_amount IS NULL OR to_amount > 0"),
    ("account_transfers", "ck_account_transfers_from_side", "(from_currency IS NULL) = (from_amount IS NULL)"),
    ("account_transfers", "ck_account_transfers_to_side", "(to_currency IS NULL) = (to_amount IS NULL)"),
    ("account_transfers", "ck_account_transfers_any_side", "from_currency IS NOT NULL OR to_currency IS NOT NULL"),
    ("account_transfers", "ck_account_transfers_currencies_differ", "from_currency IS DISTINCT FROM to_currency"),
    (
        "account_transfers",
        "ck_account_transfers_from_currency",
        f"from_currency IS NULL OR from_currency IN {CURRENCIES}",
    ),
    ("account_transfers", "ck_account_transfers_to_currency", f"to_currency IS NULL OR to_currency IN {CURRENCIES}"),
    ("payment_requisites", "ck_payment_requisites_currency", f"currency IN {CURRENCIES}"),
    ("payment_requisites", "ck_payment_requisites_kind", "kind IN ('card', 'account')"),
    # Тарифы платформы и объявления
    ("plan_requests", "ck_plan_requests_plan", "plan IN ('pro', 'max', 'individual')"),
    ("plan_requests", "ck_plan_requests_status", "status IN ('pending', 'approved', 'rejected')"),
    ("plan_requests", "ck_plan_requests_months", "months BETWEEN 1 AND 36"),
    (
        "announcements",
        "ck_announcements_category",
        "category IN ('news', 'meeting', 'emergency', 'cleanup', 'finance')",
    ),
]


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("entity", sa.String(length=30), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_fund_id", "audit_events", ["fund_id"], unique=False)
    op.create_index("ix_audit_events_actor_id", "audit_events", ["actor_id"], unique=False)
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"], unique=False)

    op.add_column("expenses", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("expenses", sa.Column("deleted_by_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_expenses_deleted_by_id_users", "expenses", "users", ["deleted_by_id"], ["id"], ondelete="SET NULL"
    )

    for table, name, condition in CHECKS:
        op.create_check_constraint(name, table, condition)

    op.create_index(
        "uq_fund_members_one_chairman",
        "fund_members",
        ["fund_id"],
        unique=True,
        postgresql_where=sa.text("role = 'chairman'"),
    )
    op.create_index(
        "uq_plan_requests_one_pending",
        "plan_requests",
        ["fund_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index("uq_plan_requests_one_pending", table_name="plan_requests")
    op.drop_index("uq_fund_members_one_chairman", table_name="fund_members")

    for table, name, _ in reversed(CHECKS):
        op.drop_constraint(name, table, type_="check")

    op.drop_constraint("fk_expenses_deleted_by_id_users", "expenses", type_="foreignkey")
    op.drop_column("expenses", "deleted_by_id")
    op.drop_column("expenses", "deleted_at")

    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_id", table_name="audit_events")
    op.drop_index("ix_audit_events_fund_id", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")

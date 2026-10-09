"""initial schema

Revision ID: b1c2d3e4f5a6
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b1c2d3e4f5a6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("avatar_url", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("is_platform_admin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)
    op.create_table(
        "funds",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=12), nullable=False),
        sa.Column("base_currency", sa.String(length=3), server_default="tjs", nullable=False),
        sa.Column("monthly_rate", sa.Integer(), server_default="0", nullable=False),
        sa.Column("start_period", sa.String(length=7), nullable=False),
        sa.Column("plan", sa.String(length=20), server_default="free", nullable=False),
        sa.Column("plan_expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("member_limit", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_funds_code"), "funds", ["code"], unique=True)
    op.create_index(op.f("ix_funds_created_by_id"), "funds", ["created_by_id"], unique=False)
    op.create_index(op.f("ix_funds_name"), "funds", ["name"], unique=False)
    op.create_table(
        "user_auth_providers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("provider_user_id", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_user_auth_providers_provider_provider_user_id"),
    )
    op.create_index(op.f("ix_user_auth_providers_user_id"), "user_auth_providers", ["user_id"], unique=False)
    op.create_table(
        "account_transfers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("from_currency", sa.String(length=3), nullable=True),
        sa.Column("from_amount", sa.Integer(), nullable=True),
        sa.Column("to_currency", sa.String(length=3), nullable=True),
        sa.Column("to_amount", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_by_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_account_transfers_created_at"), "account_transfers", ["created_at"], unique=False)
    op.create_index(op.f("ix_account_transfers_fund_id"), "account_transfers", ["fund_id"], unique=False)
    op.create_table(
        "fund_accounts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fund_id", "currency", name="uq_fund_accounts_fund_id_currency"),
    )
    op.create_index(op.f("ix_fund_accounts_fund_id"), "fund_accounts", ["fund_id"], unique=False)
    op.create_table(
        "fund_members",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=20), server_default="resident", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("address_unit", sa.String(length=50), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", sa.BigInteger(), nullable=True),
        sa.Column("joined_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fund_id", "user_id", name="uq_fund_members_fund_id_user_id"),
    )
    op.create_index(op.f("ix_fund_members_fund_id"), "fund_members", ["fund_id"], unique=False)
    op.create_index(op.f("ix_fund_members_status"), "fund_members", ["status"], unique=False)
    op.create_index(op.f("ix_fund_members_user_id"), "fund_members", ["user_id"], unique=False)
    op.create_table(
        "payment_requisites",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("bank_name", sa.String(length=100), nullable=False),
        sa.Column("card_or_account_number", sa.String(length=50), nullable=False),
        sa.Column("recipient_name", sa.String(length=120), nullable=False),
        sa.Column("phone_number", sa.String(length=30), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_requisites_fund_id"), "payment_requisites", ["fund_id"], unique=False)
    op.create_table(
        "plan_requests",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("plan", sa.String(length=20), nullable=False),
        sa.Column("months", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("admin_comment", sa.Text(), nullable=True),
        sa.Column("requested_by_id", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_by_id", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plan_requests_created_at"), "plan_requests", ["created_at"], unique=False)
    op.create_index(op.f("ix_plan_requests_fund_id"), "plan_requests", ["fund_id"], unique=False)
    op.create_index(op.f("ix_plan_requests_status"), "plan_requests", ["status"], unique=False)
    op.create_table(
        "target_funds",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("category", sa.String(length=30), server_default="landscaping", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_target_funds_created_at"), "target_funds", ["created_at"], unique=False)
    op.create_index(op.f("ix_target_funds_created_by_id"), "target_funds", ["created_by_id"], unique=False)
    op.create_index(op.f("ix_target_funds_fund_id"), "target_funds", ["fund_id"], unique=False)
    op.create_table(
        "announcements",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=20), server_default="news", nullable=False),
        sa.Column("is_pinned", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("transfer_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transfer_id"], ["account_transfers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_announcements_author_id"), "announcements", ["author_id"], unique=False)
    op.create_index(op.f("ix_announcements_created_at"), "announcements", ["created_at"], unique=False)
    op.create_index(op.f("ix_announcements_fund_id"), "announcements", ["fund_id"], unique=False)
    op.create_table(
        "contributions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("user_unit", sa.String(length=50), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("requisite_id", sa.BigInteger(), nullable=True),
        sa.Column("category", sa.String(length=20), server_default="monthly_fee", nullable=False),
        sa.Column("target_fund_id", sa.BigInteger(), nullable=True),
        sa.Column("billing_period", sa.String(length=7), nullable=True),
        sa.Column("receipt_image", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("comment_user", sa.Text(), nullable=True),
        sa.Column("comment_admin", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requisite_id"], ["payment_requisites.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_fund_id"], ["target_funds.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contributions_created_at"), "contributions", ["created_at"], unique=False)
    op.create_index(op.f("ix_contributions_currency"), "contributions", ["currency"], unique=False)
    op.create_index(op.f("ix_contributions_fund_id"), "contributions", ["fund_id"], unique=False)
    op.create_index(op.f("ix_contributions_status"), "contributions", ["status"], unique=False)
    op.create_index(op.f("ix_contributions_target_fund_id"), "contributions", ["target_fund_id"], unique=False)
    op.create_index(op.f("ix_contributions_user_id"), "contributions", ["user_id"], unique=False)
    op.create_table(
        "expenses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("receipt_images", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("target_fund_id", sa.BigInteger(), nullable=True),
        sa.Column("created_by_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_fund_id"], ["target_funds.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_expenses_category"), "expenses", ["category"], unique=False)
    op.create_index(op.f("ix_expenses_created_at"), "expenses", ["created_at"], unique=False)
    op.create_index(op.f("ix_expenses_created_by_id"), "expenses", ["created_by_id"], unique=False)
    op.create_index(op.f("ix_expenses_currency"), "expenses", ["currency"], unique=False)
    op.create_index(op.f("ix_expenses_fund_id"), "expenses", ["fund_id"], unique=False)
    op.create_index(op.f("ix_expenses_target_fund_id"), "expenses", ["target_fund_id"], unique=False)
    op.create_table(
        "announcement_comments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("announcement_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("user_unit", sa.String(length=50), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_announcement_comments_announcement_id"), "announcement_comments", ["announcement_id"], unique=False
    )
    op.create_index(op.f("ix_announcement_comments_user_id"), "announcement_comments", ["user_id"], unique=False)
    op.create_table(
        "announcement_likes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("announcement_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("announcement_id", "user_id", name="uq_announcement_likes_announcement_id_user_id"),
    )
    op.create_index(
        op.f("ix_announcement_likes_announcement_id"), "announcement_likes", ["announcement_id"], unique=False
    )
    op.create_index(op.f("ix_announcement_likes_user_id"), "announcement_likes", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_announcement_likes_user_id"), table_name="announcement_likes")
    op.drop_index(op.f("ix_announcement_likes_announcement_id"), table_name="announcement_likes")
    op.drop_table("announcement_likes")
    op.drop_index(op.f("ix_announcement_comments_user_id"), table_name="announcement_comments")
    op.drop_index(op.f("ix_announcement_comments_announcement_id"), table_name="announcement_comments")
    op.drop_table("announcement_comments")
    op.drop_index(op.f("ix_expenses_target_fund_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_fund_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_currency"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_created_by_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_created_at"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_category"), table_name="expenses")
    op.drop_table("expenses")
    op.drop_index(op.f("ix_contributions_user_id"), table_name="contributions")
    op.drop_index(op.f("ix_contributions_target_fund_id"), table_name="contributions")
    op.drop_index(op.f("ix_contributions_status"), table_name="contributions")
    op.drop_index(op.f("ix_contributions_fund_id"), table_name="contributions")
    op.drop_index(op.f("ix_contributions_currency"), table_name="contributions")
    op.drop_index(op.f("ix_contributions_created_at"), table_name="contributions")
    op.drop_table("contributions")
    op.drop_index(op.f("ix_announcements_fund_id"), table_name="announcements")
    op.drop_index(op.f("ix_announcements_created_at"), table_name="announcements")
    op.drop_index(op.f("ix_announcements_author_id"), table_name="announcements")
    op.drop_table("announcements")
    op.drop_index(op.f("ix_target_funds_fund_id"), table_name="target_funds")
    op.drop_index(op.f("ix_target_funds_created_by_id"), table_name="target_funds")
    op.drop_index(op.f("ix_target_funds_created_at"), table_name="target_funds")
    op.drop_table("target_funds")
    op.drop_index(op.f("ix_plan_requests_status"), table_name="plan_requests")
    op.drop_index(op.f("ix_plan_requests_fund_id"), table_name="plan_requests")
    op.drop_index(op.f("ix_plan_requests_created_at"), table_name="plan_requests")
    op.drop_table("plan_requests")
    op.drop_index(op.f("ix_payment_requisites_fund_id"), table_name="payment_requisites")
    op.drop_table("payment_requisites")
    op.drop_index(op.f("ix_fund_members_user_id"), table_name="fund_members")
    op.drop_index(op.f("ix_fund_members_status"), table_name="fund_members")
    op.drop_index(op.f("ix_fund_members_fund_id"), table_name="fund_members")
    op.drop_table("fund_members")
    op.drop_index(op.f("ix_fund_accounts_fund_id"), table_name="fund_accounts")
    op.drop_table("fund_accounts")
    op.drop_index(op.f("ix_account_transfers_fund_id"), table_name="account_transfers")
    op.drop_index(op.f("ix_account_transfers_created_at"), table_name="account_transfers")
    op.drop_table("account_transfers")
    op.drop_index(op.f("ix_user_auth_providers_user_id"), table_name="user_auth_providers")
    op.drop_table("user_auth_providers")
    op.drop_index(op.f("ix_funds_name"), table_name="funds")
    op.drop_index(op.f("ix_funds_created_by_id"), table_name="funds")
    op.drop_index(op.f("ix_funds_code"), table_name="funds")
    op.drop_table("funds")
    op.drop_index(op.f("ix_users_phone"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

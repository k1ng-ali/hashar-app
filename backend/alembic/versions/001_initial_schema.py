"""Initial schema for Fund App

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-06 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.String(50), primary_key=True, index=True),
        sa.Column("phone", sa.String(30), unique=True, index=True, nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("address_unit", sa.String(50), nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="RESIDENT"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("avatar_url", sa.String(255), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # 2. billing_rates
    op.create_table(
        "billing_rates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
        sa.Column("amount", sa.Integer(), nullable=False, server_default="1500"),
        sa.Column("effective_from", sa.String(20), nullable=False, server_default="2026-01-01"),
        sa.Column("created_by_admin_id", sa.String(50), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # 3. target_funds
    op.create_table(
        "target_funds",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_amount", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="Благоустройство"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_admin_id", sa.String(50), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # 4. payment_requisites
    op.create_table(
        "payment_requisites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
        sa.Column("bank_name", sa.String(100), nullable=False),
        sa.Column("card_or_account_number", sa.String(50), nullable=False),
        sa.Column("recipient_name", sa.String(120), nullable=False),
        sa.Column("phone_number", sa.String(30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("note", sa.Text(), nullable=True),
    )

    # 5. contributions
    op.create_table(
        "contributions",
        sa.Column("id", sa.String(50), primary_key=True, index=True),
        sa.Column("user_id", sa.String(50), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_name", sa.String(120), nullable=False),
        sa.Column("user_unit", sa.String(50), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False, server_default="MONTHLY_FEE"),
        sa.Column("target_fund_id", sa.Integer(), sa.ForeignKey("target_funds.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_fund_title", sa.String(200), nullable=True),
        sa.Column("billing_period", sa.String(20), nullable=True),
        sa.Column("receipt_image_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING", index=True),
        sa.Column("comment_user", sa.Text(), nullable=True),
        sa.Column("comment_admin", sa.Text(), nullable=True),
        sa.Column("reviewed_by_admin_id", sa.String(50), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_by_admin_name", sa.String(120), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, index=True),
    )

    # 6. expenses
    op.create_table(
        "expenses",
        sa.Column("id", sa.String(50), primary_key=True, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("receipt_image_paths", sa.JSON(), nullable=True),
        sa.Column("target_fund_id", sa.Integer(), sa.ForeignKey("target_funds.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_fund_title", sa.String(200), nullable=True),
        sa.Column("created_by_admin_id", sa.String(50), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_admin_name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True, index=True),
    )

    # 7. announcements
    op.create_table(
        "announcements",
        sa.Column("id", sa.String(50), primary_key=True, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="Новости"),
        sa.Column("image_urls", sa.JSON(), nullable=True),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("author_id", sa.String(50), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_name", sa.String(120), nullable=False),
        sa.Column("author_role", sa.String(50), nullable=False, server_default="Совет дома"),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("liked_by_user_ids", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, index=True),
    )

    # 8. announcement_comments
    op.create_table(
        "announcement_comments",
        sa.Column("id", sa.String(50), primary_key=True, index=True),
        sa.Column("announcement_id", sa.String(50), sa.ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.String(50), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_name", sa.String(120), nullable=False),
        sa.Column("user_unit", sa.String(50), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("announcement_comments")
    op.drop_table("announcements")
    op.drop_table("expenses")
    op.drop_table("contributions")
    op.drop_table("payment_requisites")
    op.drop_table("target_funds")
    op.drop_table("billing_rates")
    op.drop_table("users")

"""plan_discounts.max_months и plan_requests.discount_months: скидка действует ограниченное число месяцев

Revision ID: a2f3c4d5e6b7
Revises: a1f2c3d4e5b6
"""

import sqlalchemy as sa
from alembic import op

revision = "a2f3c4d5e6b7"
down_revision = "a1f2c3d4e5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plan_discounts", sa.Column("max_months", sa.Integer(), nullable=True))
    op.add_column("plan_requests", sa.Column("discount_months", sa.Integer(), server_default="0", nullable=False))
    # Ожидающие заявки уже обещаны председателю со скидкой на весь срок
    op.execute("UPDATE plan_requests SET discount_months = months WHERE discount_id IS NOT NULL AND status = 'pending'")


def downgrade() -> None:
    op.drop_column("plan_requests", "discount_months")
    op.drop_column("plan_discounts", "max_months")

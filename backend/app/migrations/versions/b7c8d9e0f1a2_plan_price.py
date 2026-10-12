"""plan price: цена текущего тарифа фонда — для переноса остатка при смене тарифа

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
"""

import sqlalchemy as sa
from alembic import op

revision = "b7c8d9e0f1a2"
down_revision = "a6b7c8d9e0f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("funds", sa.Column("plan_price", sa.Integer(), nullable=True))
    # Уже подключённые тарифы из каталога; цену individual админ укажет при следующем решении
    op.execute("UPDATE funds SET plan_price = 199 WHERE plan = 'pro'")
    op.execute("UPDATE funds SET plan_price = 399 WHERE plan = 'max'")
    op.create_check_constraint("ck_funds_plan_price", "funds", "plan_price IS NULL OR plan_price > 0")


def downgrade() -> None:
    op.drop_constraint("ck_funds_plan_price", "funds", type_="check")
    op.drop_column("funds", "plan_price")

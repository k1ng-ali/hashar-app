"""plan_prices и plan_discounts: цены, скидки и промокоды; plan_requests хранит цену на момент заявки

Revision ID: a1f2c3d4e5b6
Revises: f1a2b3c4d5e6
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a1f2c3d4e5b6"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plan_prices",
        sa.Column("plan", sa.String(length=20), nullable=False),
        sa.Column("price_tjs", sa.Integer(), nullable=False),
        sa.Column("updated_by_id", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("price_tjs > 0", name="ck_plan_prices_price_positive"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("plan"),
    )
    # Цены, которые до этого были зашиты в коде
    op.execute("INSERT INTO plan_prices (plan, price_tjs) VALUES ('pro', 199), ('max', 399)")

    op.create_table(
        "plan_discounts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=True),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("plans", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("starts_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ends_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_by_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("kind IN ('percent', 'fixed')", name="ck_plan_discounts_kind"),
        sa.CheckConstraint("value > 0", name="ck_plan_discounts_value_positive"),
        sa.CheckConstraint("kind <> 'percent' OR value < 100", name="ck_plan_discounts_percent_range"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_plan_discounts_code"),
    )

    op.add_column("plan_requests", sa.Column("list_price_tjs", sa.Integer(), nullable=True))
    op.add_column("plan_requests", sa.Column("price_tjs", sa.Integer(), nullable=True))
    op.add_column("plan_requests", sa.Column("discount_id", sa.BigInteger(), nullable=True))
    op.add_column("plan_requests", sa.Column("discount_label", sa.String(length=100), nullable=True))
    op.create_foreign_key(
        "fk_plan_requests_discount_id", "plan_requests", "plan_discounts", ["discount_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_plan_requests_discount_id", "plan_requests", ["discount_id"], unique=False)

    # Ожидающие заявки подавались по текущему прайсу
    op.execute(
        """
        UPDATE plan_requests AS r
        SET list_price_tjs = p.price_tjs, price_tjs = p.price_tjs
        FROM plan_prices AS p
        WHERE r.plan = p.plan AND r.status = 'pending'
        """
    )


def downgrade() -> None:
    op.drop_index("ix_plan_requests_discount_id", table_name="plan_requests")
    op.drop_constraint("fk_plan_requests_discount_id", "plan_requests", type_="foreignkey")
    op.drop_column("plan_requests", "discount_label")
    op.drop_column("plan_requests", "discount_id")
    op.drop_column("plan_requests", "price_tjs")
    op.drop_column("plan_requests", "list_price_tjs")
    op.drop_table("plan_discounts")
    op.drop_table("plan_prices")

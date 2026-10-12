"""requisite kind: card or account

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
"""

import sqlalchemy as sa
from alembic import op

revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payment_requisites", sa.Column("kind", sa.String(length=10), server_default="card", nullable=False))
    # Существующие реквизиты: 16 цифр — карта, остальное — счёт
    op.execute(
        "UPDATE payment_requisites SET kind = 'account' "
        "WHERE length(regexp_replace(card_or_account_number, '\\D', '', 'g')) <> 16"
    )


def downgrade() -> None:
    op.drop_column("payment_requisites", "kind")

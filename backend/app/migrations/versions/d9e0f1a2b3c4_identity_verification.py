"""identity verification: коды из SMS, подтверждённые устройства, users.verified_at

Аккаунты с привязанным Google считаются подтверждёнными: Google уже подтвердил личность.
Остальные подтвердят её при следующем входе — кодом из SMS (+992) или через Google.

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
"""

import sqlalchemy as sa
from alembic import op

revision = "d9e0f1a2b3c4"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("verified_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.execute(
        "UPDATE users SET verified_at = now() "
        "WHERE deleted_at IS NULL AND id IN (SELECT user_id FROM user_auth_providers WHERE provider = 'google')"
    )

    op.create_table(
        "verification_codes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_codes_user_id", "verification_codes", ["user_id"])

    op.create_table(
        "trusted_devices",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_trusted_devices_token_hash"),
    )
    op.create_index("ix_trusted_devices_user_id", "trusted_devices", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_trusted_devices_user_id", table_name="trusted_devices")
    op.drop_table("trusted_devices")
    op.drop_index("ix_verification_codes_user_id", table_name="verification_codes")
    op.drop_table("verification_codes")
    op.drop_column("users", "verified_at")

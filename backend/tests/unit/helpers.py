from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.enums import FundRoleEnum
from app.schemas.member import FundContext

# Настоящий PNG 1×1 — проходит проверку чеков (core/receipts.py)
RECEIPT = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def make_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.delete = AsyncMock()
    return db


def make_user(id: int = 1, **extra):
    fields = dict(
        id=id,
        full_name=f"User {id}",
        phone=f"+7900000000{id}",
        email=None,
        avatar_url=None,
        hashed_password=None,
        is_platform_admin=False,
        created_at=datetime.now(timezone.utc),
    )
    fields.update(extra)
    return SimpleNamespace(**fields)


def make_fund(id: int = 1, **extra):
    fields = dict(
        id=id,
        name="Fund",
        code="TESTCODE",
        base_currency="tjs",
        start_period="2026-07",
        plan="free",
        plan_expires_at=None,
        plan_price=None,
        member_limit=None,
    )
    fields.update(extra)
    return SimpleNamespace(**fields)


def make_member(id: int = 1, user=None, role: str = "resident", status: str = "active", **extra):
    user = user or make_user()
    fields = dict(
        id=id,
        fund_id=1,
        user_id=user.id,
        user=user,
        role=role,
        status=status,
        address_unit="кв. 1",
        message=None,
        joined_at=None,
        left_at=None,
        blocked_at=None,
        created_at=datetime.now(timezone.utc),
    )
    fields.update(extra)
    return SimpleNamespace(**fields)


def make_ctx(user_id: int = 1, role: FundRoleEnum = FundRoleEnum.resident, fund_id: int = 1) -> FundContext:
    return FundContext(fund_id=fund_id, user_id=user_id, member_id=user_id, role=role)


def make_requisite(currency: str = "tjs", **extra):
    fields = dict(
        id=1,
        fund_id=1,
        currency=currency,
        is_active=True,
        bank_name="Bank",
        card_or_account_number="1111 2222",
        recipient_name="Fund",
    )
    fields.update(extra)
    return SimpleNamespace(**fields)


def make_contribution(id: int = 1, status: str = "pending", user=None, **extra):
    user = user or make_user()
    fields = dict(
        id=id,
        fund_id=1,
        user_id=user.id,
        user=user,
        user_unit="кв. 1",
        amount=150,
        currency="tjs",
        credited_amount=150,
        credited_currency="tjs",
        requisite_id=1,
        requisite_label="Bank · 1111 2222 · Fund",
        category="monthly_fee",
        target_fund_id=None,
        target_fund=None,
        billing_period="2026-09",
        receipt_image=RECEIPT,
        status=status,
        comment_user=None,
        comment_admin=None,
        reviewed_by_id=None,
        reviewed_by=None,
        reviewed_at=None,
        created_at=datetime.now(timezone.utc),
    )
    fields.update(extra)
    return SimpleNamespace(**fields)

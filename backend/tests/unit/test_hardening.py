"""Защита перед продакшеном: чеки, самоодобрение, блокировка настроек, сессии, аудит, лимиты."""

import base64
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core import receipts
from app.core.middleware import BodySizeLimitMiddleware
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import create_refresh_token, decode_token, hash_password
from app.enums import CurrencyEnum, FundRoleEnum
from app.repositories.base_repo import like_pattern
from app.schemas.auth import LoginIn
from app.schemas.contribution import ContributionCreateIn
from app.schemas.fund import FundUpdateIn
from app.services import auth_service
from app.services.auth_service import AuthService
from app.services.contribution_service import ContributionService
from app.services.expense_service import ExpenseService
from app.services.fund_service import FundService
from app.services.target_fund_service import TargetFundService
from tests.unit.helpers import RECEIPT, make_contribution, make_ctx, make_db, make_fund, make_user


def payload_with(receipt: str) -> ContributionCreateIn:
    return ContributionCreateIn(requisite_id=1, amount=100, receipt_image=receipt)


# ─── Чеки ─────────────────────────────────────────────────────────────────────


def test_receipt_png_accepted():
    assert payload_with(RECEIPT).receipt_image == RECEIPT


@pytest.mark.parametrize(
    "receipt",
    [
        "javascript:alert(document.cookie)",
        "https://evil.example/receipt.png",
        "data:text/html;base64,PHNjcmlwdD4=",
        # Заявлен PNG, а внутри не PNG
        "data:image/png;base64," + base64.b64encode(b"<html><script>x</script></html>").decode(),
    ],
)
def test_receipt_rejects_non_images(receipt):
    with pytest.raises(ValidationError):
        payload_with(receipt)


def test_receipt_rejects_too_large():
    data = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * (receipts.MAX_RECEIPT_BYTES + 10)).decode()
    with pytest.raises(ValidationError):
        payload_with(f"data:image/png;base64,{data}")


def test_receipt_svg_only_in_dev_mode(monkeypatch):
    svg = "data:image/svg+xml;utf8,%3Csvg%3E%3C/svg%3E"
    monkeypatch.setattr(receipts.settings, "DEV_MODE", True)
    assert payload_with(svg).receipt_image == svg

    monkeypatch.setattr(receipts.settings, "DEV_MODE", False)
    with pytest.raises(ValidationError):
        payload_with(svg)


# ─── Самоодобрение чека ───────────────────────────────────────────────────────


def review_service(contribution):
    db = make_db()
    service = ContributionService(db=db)
    service.repo.get = AsyncMock(return_value=contribution)
    return db, service


async def test_cannot_approve_own_contribution():
    db, service = review_service(make_contribution(user=make_user(id=5)))
    service.member_repo.has_other_council = AsyncMock(return_value=True)

    with pytest.raises(HTTPException) as exc:
        await service.approve(fund_id=1, contribution_id=1, reviewer_id=5)

    assert exc.value.status_code == 403
    db.commit.assert_not_called()


async def test_sole_council_member_can_approve_own_contribution():
    # Совет из одного человека — иначе его взносы не одобрил бы никто
    contribution = make_contribution(user=make_user(id=5))
    db, service = review_service(contribution)
    service.member_repo.has_other_council = AsyncMock(return_value=False)

    await service.approve(fund_id=1, contribution_id=1, reviewer_id=5)

    assert contribution.status == "approved"
    db.commit.assert_awaited_once()


async def test_approve_writes_audit_event():
    contribution = make_contribution(user=make_user(id=2))
    db, service = review_service(contribution)

    await service.approve(fund_id=1, contribution_id=1, reviewer_id=5)

    event = db.add.call_args.args[0]
    assert (event.action, event.actor_id, event.entity_id) == ("contribution.approved", 5, contribution.id)


# ─── Блокировка финансовых настроек ───────────────────────────────────────────


def settings_service(has_fees: bool):
    db = make_db()
    service = FundService(db=db)
    service.repo.get = AsyncMock(return_value=make_fund(base_currency="tjs", start_period="2026-07"))
    service.contribution_repo.has_monthly_fees = AsyncMock(return_value=has_fees)
    service.accounts.ensure_active_currency = AsyncMock()
    service._fund_out = AsyncMock(return_value=None)
    return db, service


@pytest.mark.parametrize(
    "payload",
    [FundUpdateIn(base_currency=CurrencyEnum.usd), FundUpdateIn(start_period="2026-01")],
)
async def test_financial_setup_locked_after_first_fee(payload):
    db, service = settings_service(has_fees=True)

    with pytest.raises(HTTPException) as exc:
        await service.update(ctx=make_ctx(role=FundRoleEnum.chairman), payload=payload)

    assert exc.value.status_code == 409
    db.commit.assert_not_called()


async def test_base_currency_can_change_before_first_fee():
    db, service = settings_service(has_fees=False)

    await service.update(ctx=make_ctx(role=FundRoleEnum.chairman), payload=FundUpdateIn(base_currency=CurrencyEnum.usd))

    fund = await service.repo.get(1)
    assert fund.base_currency == "usd"
    db.commit.assert_awaited_once()


async def test_same_currency_is_not_a_change():
    _, service = settings_service(has_fees=True)

    await service.update(ctx=make_ctx(role=FundRoleEnum.chairman), payload=FundUpdateIn(base_currency=CurrencyEnum.tjs))


# ─── Сессии входа ─────────────────────────────────────────────────────────────


def make_session(id: int = 10, user_id: int = 7, **extra):
    fields = dict(
        id=id,
        user_id=user_id,
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        last_used_at=None,
    )
    fields.update(extra)
    return SimpleNamespace(**fields)


def auth_with_session(session):
    db = make_db()
    service = AuthService(db=db)
    service.session_repo.get = AsyncMock(return_value=session)
    service.repo.get = AsyncMock(return_value=make_user(id=7))
    return db, service


async def test_refresh_extends_live_session():
    session = make_session()
    _, service = auth_with_session(session)

    token, refresh_token = await service.refresh(create_refresh_token(user_id=7, session_id=10))

    assert decode_token(refresh_token, expected_type="refresh")["sid"] == 10
    assert session.expires_at > datetime.now(timezone.utc) + timedelta(days=29)
    assert token.user.id == 7


@pytest.mark.parametrize(
    "session",
    [
        make_session(revoked_at=datetime.now(timezone.utc)),
        make_session(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)),
        make_session(user_id=8),  # сессия чужого пользователя
        None,
    ],
)
async def test_refresh_rejects_dead_session(session):
    _, service = auth_with_session(session)

    with pytest.raises(HTTPException) as exc:
        await service.refresh(create_refresh_token(user_id=7, session_id=10))

    assert exc.value.status_code == 401


async def test_logout_revokes_session():
    session = make_session()
    db, service = auth_with_session(session)

    await service.logout(create_refresh_token(user_id=7, session_id=10))

    assert session.revoked_at is not None
    db.commit.assert_awaited_once()


async def test_login_is_rate_limited(monkeypatch):
    monkeypatch.setattr(auth_service, "LOGIN_FAILURES_BY_LOGIN", SlidingWindowLimiter(limit=3, window_seconds=60))
    monkeypatch.setattr(auth_service, "LOGIN_FAILURES_BY_IP", SlidingWindowLimiter(limit=100, window_seconds=60))
    service = AuthService(db=make_db())
    service.repo.get_by_login = AsyncMock(return_value=make_user(hashed_password=hash_password("secret1")))
    wrong = LoginIn(login="+79000000001", password="wrong")

    for _ in range(3):
        with pytest.raises(HTTPException) as exc:
            await service.login(wrong, client_ip="1.2.3.4")
        assert exc.value.status_code == 401
    # Даже верный пароль не проверяется, пока перебор заблокирован
    with pytest.raises(HTTPException) as exc:
        await service.login(LoginIn(login="+79000000001", password="secret1"), client_ip="1.2.3.4")
    assert exc.value.status_code == 429


# ─── Расходы и сборы ──────────────────────────────────────────────────────────


async def test_expense_delete_is_soft_and_audited():
    db = make_db()
    service = ExpenseService(db=db)
    expense = SimpleNamespace(id=3, title="Ремонт", amount=500, currency="tjs", deleted_at=None, deleted_by_id=None)
    service.repo.get = AsyncMock(return_value=expense)

    await service.delete(fund_id=1, expense_id=3, user_id=9)

    assert expense.deleted_at is not None and expense.deleted_by_id == 9
    db.delete.assert_not_called()
    assert db.add.call_args.args[0].action == "expense.delete"


async def test_target_fund_with_operations_cannot_be_deleted():
    db = make_db()
    service = TargetFundService(db=db)
    service.repo.get = AsyncMock(return_value=SimpleNamespace(id=4, title="Шлагбаум"))
    service.contribution_repo.exists_for_target_fund = AsyncMock(return_value=True)
    service.expense_repo.exists_for_target_fund = AsyncMock(return_value=False)

    with pytest.raises(HTTPException) as exc:
        await service.delete(fund_id=1, target_fund_id=4, user_id=9)

    assert exc.value.status_code == 409
    db.delete.assert_not_called()


# ─── Инфраструктура ───────────────────────────────────────────────────────────


def test_body_size_limit():
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=100)

    @app.post("/echo")
    async def echo(payload: dict):
        return payload

    client = TestClient(app)
    assert client.post("/echo", json={"a": 1}).status_code == 200
    assert client.post("/echo", json={"a": "x" * 200}).status_code == 413


def test_like_pattern_escapes_wildcards():
    assert like_pattern("50%_off") == "%50\\%\\_off%"

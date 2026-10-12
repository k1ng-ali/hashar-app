"""Перенос остатка тарифа при смене, скрытие чужих чеков, CSV только для совета."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.plans import PLAN_MONTH, carryover
from app.deps.fund import get_fund_context
from app.enums import FundRoleEnum
from app.main import app
from app.schemas.plan import PlanApproveIn
from app.services.dashboard_service import DashboardService
from app.services.plan_service import PlanService, plan_request_out
from app.services.target_fund_service import TargetFundService
from tests.unit.helpers import make_contribution, make_ctx, make_db, make_fund, make_user

NOW = datetime(2026, 10, 12, tzinfo=timezone.utc)


def paid_fund(plan: str, price: int | None, days_left: float, **extra):
    return make_fund(
        plan=plan, plan_price=price, plan_expires_at=datetime.now(timezone.utc) + timedelta(days=days_left), **extra
    )


def make_request(plan: str, fund, months: int = 1, status: str = "pending"):
    return SimpleNamespace(
        id=1, fund_id=fund.id, fund=fund, plan=plan, months=months, status=status, contact="+992", comment=None,
        admin_comment=None, requested_by=None, reviewed_at=None, created_at=NOW,
    )  # fmt: skip


def plan_service(request):
    db = make_db()
    service = PlanService(db=db)
    service.repo.get = AsyncMock(return_value=request)
    service.fund_repo.get = AsyncMock(return_value=request.fund)
    return db, service


# ─── Расчёт остатка ───────────────────────────────────────────────────────────


def test_carryover_converts_by_price_ratio():
    # 15 дней Max (399/мес) ≈ 199.5 смн → на Pro (199/мес) ≈ 30 дней
    fund = make_fund(plan="max", plan_price=399, plan_expires_at=NOW + timedelta(days=15))

    rest = carryover(fund, new_price=199, now=NOW)

    assert rest.value_tjs == 199.5
    assert rest.extra == timedelta(days=15) * 399 / 199


@pytest.mark.parametrize(
    "fund",
    [
        make_fund(plan="free", plan_price=None, plan_expires_at=None),
        make_fund(plan="pro", plan_price=199, plan_expires_at=NOW - timedelta(days=1)),  # истёк
        make_fund(plan="pro", plan_price=199, plan_expires_at=None),  # бессрочный вручную
        make_fund(plan="individual", plan_price=None, plan_expires_at=NOW + timedelta(days=5)),  # цена неизвестна
    ],
)
def test_nothing_to_carry_over(fund):
    assert carryover(fund, new_price=199, now=NOW) is None


# ─── Решение админа ───────────────────────────────────────────────────────────


async def test_switch_plan_adds_converted_days():
    fund = paid_fund("pro", 199, days_left=10)
    _, service = plan_service(make_request("max", fund, months=1))

    await service.approve(request_id=1, admin_id=1, payload=PlanApproveIn())

    # 1 оплаченный месяц Max + 10 дней Pro в пересчёте на цену Max (≈ 4.99 дня)
    expected = datetime.now(timezone.utc) + PLAN_MONTH + timedelta(days=10) * 199 / 399
    assert fund.plan == "max" and fund.plan_price == 399
    assert abs(fund.plan_expires_at - expected) < timedelta(seconds=5)


async def test_same_plan_extends_from_expiry():
    fund = paid_fund("pro", 199, days_left=10)
    expires = fund.plan_expires_at
    _, service = plan_service(make_request("pro", fund, months=3))

    await service.approve(request_id=1, admin_id=1, payload=PlanApproveIn())

    assert fund.plan_expires_at == expires + PLAN_MONTH * 3


async def test_individual_requires_monthly_price():
    fund = paid_fund("pro", 199, days_left=10)
    db, service = plan_service(make_request("individual", fund))

    with pytest.raises(HTTPException) as exc:
        await service.approve(request_id=1, admin_id=1, payload=PlanApproveIn(member_limit=1000))

    assert exc.value.status_code == 422
    db.commit.assert_not_called()


async def test_individual_uses_negotiated_price():
    fund = paid_fund("max", 399, days_left=30)
    _, service = plan_service(make_request("individual", fund, months=1))

    await service.approve(request_id=1, admin_id=1, payload=PlanApproveIn(member_limit=1000, monthly_price=798))

    # Месяц Max (399) по цене 798 — это половина месяца individual
    expected = datetime.now(timezone.utc) + PLAN_MONTH + PLAN_MONTH / 2
    assert fund.plan_price == 798 and fund.member_limit == 1000
    assert abs(fund.plan_expires_at - expected) < timedelta(seconds=5)


def test_pending_request_shows_carryover_preview():
    fund = paid_fund("max", 399, days_left=15)

    out = plan_request_out(make_request("pro", fund))

    assert out.carryover_tjs == pytest.approx(199.5, abs=0.1)
    assert out.carryover_days == 30


# ─── Чужие чеки ───────────────────────────────────────────────────────────────


async def test_target_fund_hides_others_receipts():
    service = TargetFundService(db=make_db())
    service.repo.get = AsyncMock(return_value=SimpleNamespace(
        id=1, title="Шлагбаум", description="", target_amount=1000, currency="tjs", category="security",
        is_active=True, created_at=NOW,
    ))  # fmt: skip
    mine, other = make_contribution(id=1, user=make_user(id=1)), make_contribution(id=2, user=make_user(id=2))
    service.contribution_repo.collected_by_target_funds = AsyncMock(return_value={})
    service.contribution_repo.list = AsyncMock(return_value=[mine, other])
    service.contribution_repo.approved_monthly_sums = AsyncMock(return_value={})

    resident = await service.get_detail(ctx=make_ctx(user_id=1), target_fund_id=1)
    council = await service.get_detail(ctx=make_ctx(user_id=9, role=FundRoleEnum.admin), target_fund_id=1)

    assert [c.receipt_image is not None for c in resident.contributions] == [True, False]
    assert all(c.receipt_image for c in council.contributions)


async def test_operations_feed_hides_others_receipts():
    service = DashboardService(db=make_db())
    service.contribution_repo.list = AsyncMock(
        return_value=[make_contribution(id=1, user=make_user(id=1)), make_contribution(id=2, user=make_user(id=2))]
    )

    operations = await service.operations(ctx=make_ctx(user_id=1), type_filter="income")

    receipts = {op.id: op.receipt_image for op in operations}
    assert receipts["c-1"] and receipts["c-2"] is None


# ─── CSV только для совета ────────────────────────────────────────────────────


@pytest.mark.parametrize("kind", ["contributions", "expenses", "debtors"])
def test_resident_cannot_export_csv(kind):
    app.dependency_overrides[get_fund_context] = lambda: make_ctx(user_id=1, role=FundRoleEnum.resident)
    try:
        response = TestClient(app).get(f"/api/v1/council/funds/1/reports/export/{kind}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_old_export_urls_are_gone():
    app.dependency_overrides[get_fund_context] = lambda: make_ctx(user_id=1, role=FundRoleEnum.chairman)
    try:
        response = TestClient(app).get("/api/v1/funds/1/reports/export/debtors")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404

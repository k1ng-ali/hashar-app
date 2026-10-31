"""Цены из БД, распродажи и промокоды; заявка хранит цену на момент подачи."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.plans import PLAN_MONTH, discount_state, discounted_price
from app.enums import DiscountStateEnum, PlanEnum, PromoStatusEnum
from app.schemas.plan import PlanApproveIn, PlanRequestIn
from app.schemas.pricing import PlanDiscountIn
from app.services.plan_service import PlanService
from app.services.pricing_service import PricingService, ResolvedPrice
from tests.unit.helpers import make_db, make_fund

NOW = datetime.now(timezone.utc)


def make_discount(id: int = 1, code: str | None = None, kind: str = "percent", value: int = 50, **extra):
    fields = dict(
        id=id,
        title=f"Discount {id}",
        code=code,
        kind=kind,
        value=value,
        plans=["pro", "max"],
        starts_at=None,
        ends_at=None,
        max_uses=None,
        is_active=True,
        created_at=NOW,
    )
    fields.update(extra)
    return SimpleNamespace(**fields)


def pricing_service(price: int | None = 199, sales=(), promo=None, uses: int = 0, fund_uses: int = 0):
    service = PricingService(db=make_db())
    service.repo.get_price = AsyncMock(return_value=SimpleNamespace(price_tjs=price) if price else None)
    service.repo.list_running_sales = AsyncMock(return_value=list(sales))
    service.repo.get_by_code = AsyncMock(return_value=promo)
    service.repo.count_uses = AsyncMock(
        side_effect=lambda discount_id, fund_id=None: fund_uses if fund_id is not None else uses
    )
    return service


# ─── Расчёт скидки ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "price, kind, value, expected",
    [
        (199, "percent", 50, 100),
        (399, "percent", 25, 299),
        (199, "fixed", 50, 149),
        (199, "fixed", 500, 1),  # не ниже 1 смн
        (1, "percent", 99, 1),
    ],
)
def test_discounted_price(price, kind, value, expected):
    assert discounted_price(price, kind, value) == expected


@pytest.mark.parametrize(
    "extra, uses, expected",
    [
        ({}, 0, DiscountStateEnum.active),
        ({"is_active": False}, 0, DiscountStateEnum.disabled),
        ({"ends_at": NOW - timedelta(days=1)}, 0, DiscountStateEnum.expired),
        ({"starts_at": NOW + timedelta(days=1)}, 0, DiscountStateEnum.scheduled),
        ({"max_uses": 2}, 2, DiscountStateEnum.exhausted),
        ({"max_uses": 2}, 1, DiscountStateEnum.active),
    ],
)
def test_discount_state(extra, uses, expected):
    assert discount_state(make_discount(**extra), uses) == expected


# ─── Лучшая цена ──────────────────────────────────────────────────────────────


async def test_resolve_without_discounts_uses_current_price():
    resolved = await pricing_service(price=250).resolve(PlanEnum.pro, fund_id=1)

    assert (resolved.list_price, resolved.price, resolved.discount) == (250, 250, None)


async def test_resolve_picks_best_sale_for_plan():
    sales = [
        make_discount(id=1, value=10),
        make_discount(id=2, value=30),
        make_discount(id=3, value=90, plans=["max"]),  # на другой тариф
    ]

    resolved = await pricing_service(sales=sales).resolve(PlanEnum.pro, fund_id=1)

    assert resolved.discount.id == 2 and resolved.price == 139


async def test_better_promo_beats_sale():
    promo = make_discount(id=5, code="HALF", value=50)
    service = pricing_service(sales=[make_discount(id=1, value=10)], promo=promo)

    resolved = await service.resolve(PlanEnum.pro, fund_id=1, promo_code=" half ")

    service.repo.get_by_code.assert_awaited_once_with("HALF", for_update=False)
    assert resolved.discount is promo and resolved.price == 100
    assert resolved.promo_status == PromoStatusEnum.applied
    assert resolved.label == "HALF"


async def test_weaker_promo_is_not_consumed():
    sale = make_discount(id=1, value=50, title="Весна")
    service = pricing_service(sales=[sale], promo=make_discount(id=5, code="TEN", value=10))

    resolved = await service.resolve(PlanEnum.pro, fund_id=1, promo_code="TEN")

    assert resolved.discount is sale and resolved.price == 100
    assert resolved.promo_status == PromoStatusEnum.not_better
    assert resolved.label == "Весна"


@pytest.mark.parametrize(
    "promo, uses, fund_uses, code, detail",
    [
        (None, 0, 0, 404, "Promo code not found"),
        (make_discount(code="X", is_active=False), 0, 0, 404, "Promo code not found"),
        (make_discount(code="X", ends_at=NOW - timedelta(days=1)), 0, 0, 409, "Promo code has expired"),
        (make_discount(code="X", starts_at=NOW + timedelta(days=1)), 0, 0, 409, "Promo code is not active yet"),
        (make_discount(code="X", max_uses=3), 3, 0, 409, "Promo code usage limit reached"),
        (make_discount(code="X", plans=["max"]), 0, 0, 409, "Promo code is not valid for this plan"),
        (make_discount(code="X"), 1, 1, 409, "Promo code was already used by this fund"),
    ],
)
async def test_invalid_promo_rejected(promo, uses, fund_uses, code, detail):
    service = pricing_service(promo=promo, uses=uses, fund_uses=fund_uses)

    with pytest.raises(HTTPException) as exc:
        await service.resolve(PlanEnum.pro, fund_id=1, promo_code="X")

    assert exc.value.status_code == code and exc.value.detail == detail


async def test_promo_not_valid_for_individual():
    service = pricing_service(price=None, promo=make_discount(code="X"))

    with pytest.raises(HTTPException) as exc:
        await service.resolve(PlanEnum.individual, fund_id=1, promo_code="X")

    assert exc.value.status_code == 409


# ─── Витрина ──────────────────────────────────────────────────────────────────


async def test_catalog_uses_db_prices_and_running_sale():
    service = PricingService(db=make_db())
    service.repo.list_prices = AsyncMock(
        return_value=[SimpleNamespace(plan="pro", price_tjs=250), SimpleNamespace(plan="max", price_tjs=500)]
    )
    service.repo.list_running_sales = AsyncMock(return_value=[make_discount(value=20, plans=["pro"], title="Весна")])

    catalog = {option.plan: option for option in await service.catalog()}

    pro, max_plan = catalog[PlanEnum.pro], catalog[PlanEnum.max]
    assert (pro.list_price_tjs, pro.price_tjs, pro.sale.title) == (250, 200, "Весна")
    assert (max_plan.list_price_tjs, max_plan.price_tjs, max_plan.sale) == (500, 500, None)
    assert catalog[PlanEnum.free].price_tjs == 0
    assert catalog[PlanEnum.individual].price_tjs is None


# ─── Заявка ───────────────────────────────────────────────────────────────────


def plan_service_for_create(resolved: ResolvedPrice):
    service = PlanService(db=make_db())
    service.repo.has_pending = AsyncMock(return_value=False)
    service.repo.create = AsyncMock(
        side_effect=lambda **fields: SimpleNamespace(
            id=1, fund=make_fund(), status="pending", admin_comment=None, requested_by=None, reviewed_at=None,
            created_at=NOW, **fields,
        )
    )  # fmt: skip
    service.pricing.resolve = AsyncMock(return_value=resolved)
    return service


async def test_create_request_saves_price_snapshot():
    promo = make_discount(id=5, code="HALF")
    service = plan_service_for_create(
        ResolvedPrice(list_price=199, price=100, discount=promo, promo_status=PromoStatusEnum.applied)
    )

    out = await service.create_request(
        fund_id=1,
        user_id=3,
        payload=PlanRequestIn(plan=PlanEnum.pro, contact="@chairman", promo_code="half", expected_price_tjs=100),
    )

    service.pricing.resolve.assert_awaited_once_with(PlanEnum.pro, 1, "half", for_update=True)
    kwargs = service.repo.create.call_args.kwargs
    assert (kwargs["list_price_tjs"], kwargs["price_tjs"], kwargs["discount_id"]) == (199, 100, 5)
    assert out.discount_label == "HALF" and out.price_tjs == 100


async def test_create_request_rejects_stale_price():
    service = plan_service_for_create(ResolvedPrice(list_price=250, price=250))

    with pytest.raises(HTTPException) as exc:
        await service.create_request(
            fund_id=1,
            user_id=3,
            payload=PlanRequestIn(plan=PlanEnum.pro, contact="@chairman", expected_price_tjs=199),
        )

    assert exc.value.detail == "Plan price has changed"
    service.db.commit.assert_not_called()


async def test_approve_keeps_requested_price_after_price_change():
    # Заявка подана по акции за 100 смн: цена фонда и выручка считаются от неё, а не от прайса
    fund = make_fund(plan="free")
    request = SimpleNamespace(
        id=1, fund_id=fund.id, fund=fund, plan="pro", months=2, status="pending", contact="+992", comment=None,
        admin_comment=None, requested_by=None, reviewed_at=None, created_at=NOW,
        list_price_tjs=199, price_tjs=100, discount_id=5, discount_label="HALF",
    )  # fmt: skip
    service = PlanService(db=make_db())
    service.repo.get = AsyncMock(return_value=request)
    service.fund_repo.get = AsyncMock(return_value=fund)

    await service.approve(request_id=1, admin_id=1, payload=PlanApproveIn())

    assert fund.plan_price == 100
    assert abs(fund.plan_expires_at - (datetime.now(timezone.utc) + PLAN_MONTH * 2)) < timedelta(seconds=5)
    audit = service.db.add.call_args_list[0].args[0]
    assert audit.details["price"] == 100 and audit.details["discount"] == "HALF"


async def test_quote_price_change_is_not_extension():
    # Тот же тариф, но цена выросла: остаток пересчитывается, а не просто добавляются месяцы
    fund = make_fund(plan="pro", plan_price=199, plan_expires_at=datetime.now(timezone.utc) + timedelta(days=30))
    service = PlanService(db=make_db())
    service.fund_repo.get = AsyncMock(return_value=fund)
    service.pricing.resolve = AsyncMock(return_value=ResolvedPrice(list_price=398, price=398))

    quote = await service.quote(fund_id=1, plan=PlanEnum.pro, months=3)

    assert quote.is_extension is False
    assert quote.total_tjs == 1194
    assert quote.carryover_days == 15


async def test_quote_same_price_is_extension():
    fund = make_fund(plan="pro", plan_price=199, plan_expires_at=datetime.now(timezone.utc) + timedelta(days=30))
    service = PlanService(db=make_db())
    service.fund_repo.get = AsyncMock(return_value=fund)
    service.pricing.resolve = AsyncMock(return_value=ResolvedPrice(list_price=199, price=199))

    quote = await service.quote(fund_id=1, plan=PlanEnum.pro, months=1)

    assert quote.is_extension is True and quote.carryover_tjs is None


# ─── Админ платформы ──────────────────────────────────────────────────────────


async def test_set_price_writes_audit():
    service = PricingService(db=make_db())
    row = SimpleNamespace(plan="pro", price_tjs=199, updated_by_id=None, updated_at=NOW)
    service.repo.get_price = AsyncMock(return_value=row)

    out = await service.set_price(plan=PlanEnum.pro, price_tjs=249, admin_id=9)

    assert out.price_tjs == 249 and row.updated_by_id == 9
    audit = service.db.add.call_args.args[0]
    assert audit.fund_id is None and audit.action == "pricing.price"
    assert (audit.details["old_price"], audit.details["price"]) == (199, 249)
    service.db.commit.assert_awaited_once()


async def test_delete_used_discount_conflicts():
    service = PricingService(db=make_db())
    service.repo.get_discount = AsyncMock(return_value=make_discount(code="X"))
    service.repo.count_uses = AsyncMock(return_value=1)

    with pytest.raises(HTTPException) as exc:
        await service.delete_discount(discount_id=1, admin_id=9)

    assert exc.value.status_code == 409
    service.db.commit.assert_not_called()


async def test_create_duplicate_code_conflicts():
    service = PricingService(db=make_db())
    service.repo.get_by_code = AsyncMock(return_value=make_discount(code="HALF"))
    payload = PlanDiscountIn(title="Half", code="half", kind="percent", value=50, plans=["pro"])

    with pytest.raises(HTTPException) as exc:
        await service.create_discount(payload=payload, admin_id=9)

    assert exc.value.status_code == 409


@pytest.mark.parametrize(
    "fields",
    [
        {"kind": "percent", "value": 100, "plans": ["pro"]},  # бесплатный месяц — только вручную
        {"kind": "percent", "value": 10, "plans": []},
        {"kind": "percent", "value": 10, "plans": ["free"]},
        {"kind": "percent", "value": 10, "plans": ["individual"]},
        {"kind": "fixed", "value": 10, "plans": ["pro"], "code": "A B"},
        {"kind": "fixed", "value": 10, "plans": ["pro"], "max_uses": 5},  # лимит только у промокода
        {"kind": "fixed", "value": 10, "plans": ["pro"], "starts_at": NOW, "ends_at": NOW},
    ],
)
def test_discount_payload_validation(fields):
    with pytest.raises(ValidationError):
        PlanDiscountIn(title="Test", **fields)


def test_discount_code_normalized_and_blank_means_sale():
    plans = ["pro"]
    assert PlanDiscountIn(title="Весна", kind="fixed", value=1, plans=plans, code=" spring-26 ").code == "SPRING-26"
    assert PlanDiscountIn(title="Весна", kind="fixed", value=1, plans=plans, code="  ").code is None

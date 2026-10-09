from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.plans import effective_plan, member_limit
from app.enums import CurrencyEnum, FundRoleEnum, PlanEnum
from app.schemas.account import TransferCreateIn
from app.schemas.member import JoinIn
from app.services.account_service import AccountService
from app.services.fund_service import FundService
from app.services.member_service import MemberService
from app.services.plan_service import PlanService
from tests.unit.helpers import make_ctx, make_db, make_fund, make_member

# ─── Тарифы ───────────────────────────────────────────────────────────────────


def test_expired_plan_falls_back_to_free():
    fund = make_fund(plan="pro", plan_expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    assert effective_plan(fund) == PlanEnum.free
    assert member_limit(fund) == 10


def test_individual_plan_uses_custom_limit():
    fund = make_fund(plan="individual", member_limit=1000)
    assert member_limit(fund) == 1000
    assert member_limit(make_fund(plan="individual", member_limit=None)) is None


async def test_ensure_capacity_blocks_over_limit():
    service = PlanService(db=make_db())
    service.member_repo.count_active = AsyncMock(return_value=10)

    with pytest.raises(HTTPException) as exc:
        await service.ensure_capacity(make_fund(plan="free"))

    assert exc.value.status_code == 409


async def test_plan_request_only_one_pending():
    db = make_db()
    service = PlanService(db=db)
    service.repo.has_pending = AsyncMock(return_value=True)

    from app.schemas.plan import PlanRequestIn

    with pytest.raises(HTTPException) as exc:
        await service.create_request(fund_id=1, user_id=1, payload=PlanRequestIn(plan=PlanEnum.pro))

    assert exc.value.status_code == 409
    db.commit.assert_not_called()


# ─── Вступление и участники ──────────────────────────────────────────────────


async def test_join_twice_while_pending():
    service = FundService(db=make_db())
    service.repo.get = AsyncMock(return_value=make_fund())
    service.member_repo.get_by_user = AsyncMock(return_value=make_member(status="pending"))

    with pytest.raises(HTTPException) as exc:
        await service.join(fund_id=1, user_id=1, payload=JoinIn(address_unit="кв. 5"))

    assert exc.value.status_code == 409


async def test_join_blocked_member_forbidden():
    service = FundService(db=make_db())
    service.repo.get = AsyncMock(return_value=make_fund())
    service.member_repo.get_by_user = AsyncMock(return_value=make_member(status="blocked"))

    with pytest.raises(HTTPException) as exc:
        await service.join(fund_id=1, user_id=1, payload=JoinIn(address_unit="кв. 5"))

    assert exc.value.status_code == 403


async def test_chairman_cannot_leave():
    service = FundService(db=make_db())

    with pytest.raises(HTTPException) as exc:
        await service.leave(ctx=make_ctx(role=FundRoleEnum.chairman))

    assert exc.value.status_code == 409


async def test_approve_respects_plan_limit():
    db = make_db()
    service = MemberService(db=db)
    service.repo.get = AsyncMock(return_value=make_member(status="pending"))
    service.fund_repo.get = AsyncMock(return_value=make_fund(plan="free"))
    service.plans.member_repo.count_active = AsyncMock(return_value=10)

    with pytest.raises(HTTPException) as exc:
        await service.approve(fund_id=1, member_id=1, reviewer_id=2)

    assert exc.value.status_code == 409
    db.commit.assert_not_called()


async def test_cannot_change_chairman_role():
    service = MemberService(db=make_db())
    service.repo.get = AsyncMock(return_value=make_member(role="chairman", user_id=5))

    with pytest.raises(HTTPException) as exc:
        await service.set_role(fund_id=1, member_id=1, role=FundRoleEnum.resident, actor_id=1)

    assert exc.value.status_code == 403


async def test_transfer_chairman_swaps_roles():
    db = make_db()
    service = MemberService(db=db)
    target = make_member(id=2, role="admin")
    current = make_member(id=1, role="chairman")
    service.repo.get = AsyncMock(
        side_effect=lambda fund_id, member_id, for_update=False: {1: current, 2: target}[member_id]
    )

    await service.transfer_chairman(fund_id=1, member_id=2, actor_member_id=1)

    assert target.role == "chairman"
    assert current.role == "admin"
    db.commit.assert_awaited_once()


# ─── Счета ────────────────────────────────────────────────────────────────────


def test_transfer_requires_matching_sides():
    with pytest.raises(ValueError):
        TransferCreateIn(from_currency=CurrencyEnum.tjs, comment="тест")
    with pytest.raises(ValueError):
        TransferCreateIn(
            from_currency=CurrencyEnum.tjs, from_amount=1, to_currency=CurrencyEnum.tjs, to_amount=1, comment="тест"
        )
    # Корректировка — одна сторона
    TransferCreateIn(to_currency=CurrencyEnum.rub, to_amount=100, comment="Найдена наличность")


async def test_balances_combine_all_sources():
    service = AccountService(db=make_db())
    service.contribution_repo.approved_sums_by_currency = AsyncMock(return_value={"tjs": 1000, "rub": 500})
    service.expense_repo.sums_by_currency = AsyncMock(return_value={"tjs": 200})
    service.transfer_repo.sums_by_currency = AsyncMock(return_value=({"rub": 850}, {"tjs": 100}))

    balances = await service.balances(fund_id=1)

    assert balances == {"tjs": 700, "rub": 1350, "usd": 0}


async def test_cannot_disable_base_currency():
    service = AccountService(db=make_db())
    service.fund_repo.get = AsyncMock(return_value=make_fund(base_currency="tjs"))

    with pytest.raises(HTTPException) as exc:
        await service.disable_currency(fund_id=1, currency=CurrencyEnum.tjs)

    assert exc.value.status_code == 409


async def test_new_member_accrues_from_join_month():
    from app.core.finance import current_period

    service = MemberService(db=make_db())
    service.contribution_repo.monthly_sums_by_user = AsyncMock(return_value={})
    member = make_member(joined_at=datetime.now(timezone.utc))

    balances = await service._balances_for(make_fund(start_period="2020-01", monthly_rate=150), [member])

    # Вступил в этом месяце — начислен только текущий месяц, а не все с 2020 года
    assert balances[member.user_id].total_due == 150
    assert balances[member.user_id].unpaid_periods == [current_period()]

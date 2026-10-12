"""Выход, возвращение и блокировка: долг за время участия остаётся, период отсутствия решает совет."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.finance import calculate_balance, current_period, shift_period
from app.enums import MemberStatusEnum
from app.services.fund_service import FundService
from app.services.member_service import MemberService, absence_periods
from tests.unit.helpers import make_db, make_fund, make_member


def months_ago(n: int) -> datetime:
    year, month = map(int, shift_period(current_period(), -n).split("-"))
    return datetime(year, month, 15, tzinfo=timezone.utc)


def make_member_service(member):
    db = make_db()
    service = MemberService(db=db)
    service.repo.get = AsyncMock(return_value=member)
    service.fund_repo.get = AsyncMock(return_value=make_fund(plan="pro"))
    service.plans.member_repo.count_active = AsyncMock(return_value=1)
    service.pause_repo.create = AsyncMock()
    return db, service


# ─── Расчёт ───────────────────────────────────────────────────────────────────


def test_absence_is_between_leave_and_return_months():
    # Ушёл в марте, вернулся в июле: решать о апреле–июне
    assert absence_periods(datetime(2026, 3, 20, tzinfo=timezone.utc), "2026-07") == ["2026-04", "2026-05", "2026-06"]
    # Ушёл и вернулся в соседних месяцах — решать не о чем
    assert absence_periods(datetime(2026, 6, 1, tzinfo=timezone.utc), "2026-07") == []


def test_excluded_months_are_not_accrued_and_skipped_by_payments():
    schedule = [("2026-01", 100)]
    excluded = {"2026-03", "2026-04"}
    balance = calculate_balance(
        paid=300, pending=0, schedule=schedule, start_period="2026-01", today_period="2026-06", excluded=excluded
    )

    assert balance.total_due == 400  # январь, февраль, май, июнь
    assert balance.covered_periods == ["2026-01", "2026-02", "2026-05"]
    assert balance.unpaid_periods == ["2026-06"]


# ─── Выход ────────────────────────────────────────────────────────────────────


async def test_leave_keeps_member_record():
    db = make_db()
    service = FundService(db=db)
    member = make_member(role="admin", joined_at=months_ago(5))
    service.member_repo.get_by_user = AsyncMock(return_value=member)

    await service.leave(fund_id=1, user_id=1)

    assert member.status == MemberStatusEnum.left.value
    assert member.left_at is not None
    assert member.role == "resident"
    db.delete.assert_not_called()


async def test_blocked_member_can_leave_and_stays_blocked():
    service = FundService(db=make_db())
    member = make_member(status="blocked", blocked_at=months_ago(2))
    service.member_repo.get_by_user = AsyncMock(return_value=member)

    await service.leave(fund_id=1, user_id=1)

    assert member.status == "blocked"
    assert member.left_at is not None


# ─── Возвращение ──────────────────────────────────────────────────────────────


async def test_returning_member_requires_decision():
    member = make_member(status="pending", joined_at=months_ago(8), left_at=months_ago(4))
    db, service = make_member_service(member)

    with pytest.raises(HTTPException) as exc:
        await service.approve(fund_id=1, member_id=1, reviewer_id=2)

    assert exc.value.detail == "Absence decision required"
    db.commit.assert_not_called()


async def test_return_without_accrual_creates_pause_and_keeps_join_date():
    joined = months_ago(8)
    member = make_member(status="pending", joined_at=joined, left_at=months_ago(4))
    db, service = make_member_service(member)

    await service.approve(fund_id=1, member_id=1, reviewer_id=2, accrue_absence=False)

    kwargs = service.pause_repo.create.call_args.kwargs
    assert (kwargs["from_period"], kwargs["to_period"]) == (
        shift_period(current_period(), -3),
        shift_period(current_period(), -1),
    )
    assert kwargs["reason"] == "left"
    assert member.status == "active"
    assert member.joined_at == joined  # долг до ухода остаётся
    assert member.left_at is None


async def test_return_with_accrual_creates_no_pause():
    member = make_member(status="pending", joined_at=months_ago(8), left_at=months_ago(4))
    _, service = make_member_service(member)

    await service.approve(fund_id=1, member_id=1, reviewer_id=2, accrue_absence=True)

    service.pause_repo.create.assert_not_called()
    assert member.status == "active"


async def test_new_member_needs_no_decision():
    member = make_member(status="pending")
    _, service = make_member_service(member)

    await service.approve(fund_id=1, member_id=1, reviewer_id=2)

    assert member.status == "active"
    assert member.joined_at is not None


# ─── Блокировка ───────────────────────────────────────────────────────────────


async def test_unblock_requires_decision():
    member = make_member(status="blocked", joined_at=months_ago(8), blocked_at=months_ago(3))
    db, service = make_member_service(member)

    with pytest.raises(HTTPException) as exc:
        await service.set_status(fund_id=1, member_id=1, new_status=MemberStatusEnum.active, actor_id=2)

    assert exc.value.detail == "Absence decision required"
    db.commit.assert_not_called()


async def test_unblock_without_accrual_pauses_block_period():
    member = make_member(status="blocked", joined_at=months_ago(8), blocked_at=months_ago(3))
    _, service = make_member_service(member)

    await service.set_status(
        fund_id=1, member_id=1, new_status=MemberStatusEnum.active, actor_id=2, accrue_absence=False
    )

    assert service.pause_repo.create.call_args.kwargs["reason"] == "blocked"
    assert member.status == "active"
    assert member.blocked_at is None


async def test_unblock_member_who_left_is_simple():
    member = make_member(status="blocked", joined_at=months_ago(8), blocked_at=months_ago(3), left_at=months_ago(2))
    _, service = make_member_service(member)

    await service.set_status(fund_id=1, member_id=1, new_status=MemberStatusEnum.active, actor_id=2)

    # Решение о периоде отсутствия — позже, при заявке на возвращение
    service.pause_repo.create.assert_not_called()
    assert member.status == "left"
    assert member.blocked_at is not None


async def test_block_sets_date():
    member = make_member(status="active", joined_at=months_ago(8))
    _, service = make_member_service(member)

    await service.set_status(fund_id=1, member_id=1, new_status=MemberStatusEnum.blocked, actor_id=2)

    assert member.status == "blocked"
    assert member.blocked_at is not None


async def test_balance_of_absent_member_freezes_at_leave_month():
    member = make_member(status="left", joined_at=months_ago(6), left_at=months_ago(3))
    service = MemberService(db=make_db())
    service.contribution_repo.monthly_sums_by_user = AsyncMock(return_value={})
    service.rate_repo.schedule = AsyncMock(return_value=[("2020-01", 100)])
    service.pause_repo.excluded_periods = AsyncMock(return_value={})

    balance = (await service._balances_for(make_fund(start_period="2020-01"), [member]))[member.user_id]

    # С месяца вступления по месяц выхода включительно: 4 месяца
    assert balance.total_due == 400
    assert balance.current_period == shift_period(current_period(), -3)

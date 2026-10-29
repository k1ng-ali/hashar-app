"""Окончание тарифа: льготный срок, блокировка взносов, уведомления совету от платформы."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.plans import PLAN_GRACE, blocks_at, lapse_state
from app.enums import FundRoleEnum, LapseEnum
from app.models.fund_notice import FundNotice
from app.schemas.contribution import ContributionCreateIn
from app.schemas.plan import PlanApproveIn
from app.services.contribution_service import ContributionService
from app.services.notice_service import NoticeService
from app.services.plan_service import PlanService
from tests.unit.helpers import RECEIPT, make_ctx, make_db, make_fund, make_member

NOW = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)


def expired_fund(days_ago: float, **extra):
    return make_fund(plan="pro", plan_price=199, plan_expires_at=NOW - timedelta(days=days_ago), **extra)


def added_notices(db) -> list[FundNotice]:
    return [call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], FundNotice)]


# ─── Состояние тарифа ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "fund, state",
    [
        (make_fund(plan="free"), LapseEnum.none),
        (make_fund(plan="pro", plan_expires_at=None), LapseEnum.none),  # бессрочный
        (make_fund(plan="pro", plan_expires_at=NOW + timedelta(days=1)), LapseEnum.none),
        (expired_fund(1), LapseEnum.grace),
        (expired_fund(6.9), LapseEnum.grace),
        (expired_fund(7), LapseEnum.lapsed),
    ],
)
def test_lapse_state(fund, state):
    assert lapse_state(fund, NOW) == state


def test_blocks_at_is_expiry_plus_grace():
    fund = expired_fund(2)
    assert blocks_at(fund) == fund.plan_expires_at + PLAN_GRACE
    assert blocks_at(make_fund(plan="free")) is None


# ─── Кто может вносить после окончания ────────────────────────────────────────


def plans(members: int, council_ids: list[int]) -> PlanService:
    service = PlanService(db=make_db())
    service.member_repo.count_active = AsyncMock(return_value=members)
    service.member_repo.first_council_user_ids = AsyncMock(return_value=council_ids)
    return service


async def test_grace_period_does_not_block():
    # ensure_can_contribute сверяется с текущим временем, а не с NOW — иначе тест «протухает» вместе с NOW
    fund = make_fund(plan="pro", plan_price=199, plan_expires_at=datetime.now(timezone.utc) - timedelta(days=3))
    await plans(50, []).ensure_can_contribute(fund, user_id=9, role=FundRoleEnum.resident)


async def test_lapsed_fund_within_free_limit_does_not_block():
    await plans(10, []).ensure_can_contribute(expired_fund(30), user_id=9, role=FundRoleEnum.resident)


async def test_lapsed_fund_over_limit_blocks_residents():
    with pytest.raises(HTTPException) as exc:
        await plans(11, [1, 2]).ensure_can_contribute(expired_fund(8), user_id=9, role=FundRoleEnum.resident)
    assert exc.value.status_code == 403


async def test_lapsed_fund_allows_first_council_members():
    service = plans(40, [1, 2])
    await service.ensure_can_contribute(expired_fund(8), user_id=2, role=FundRoleEnum.admin)
    # Лимит считается от размера Free, а не от числа членов совета
    service.member_repo.first_council_user_ids.assert_awaited_with(1, 10)


async def test_lapsed_fund_blocks_admin_beyond_free_limit():
    # Администратор №11 — раздачей прав лимит Free не обойти
    with pytest.raises(HTTPException) as exc:
        await plans(40, list(range(1, 11))).ensure_can_contribute(expired_fund(8), user_id=11, role=FundRoleEnum.admin)
    assert exc.value.status_code == 403


async def test_info_reports_block_for_resident_and_council():
    fund = expired_fund(9)

    resident = await plans(20, [1]).info(fund, user_id=9, role=FundRoleEnum.resident)
    chairman = await plans(20, [1]).info(fund, user_id=1, role=FundRoleEnum.chairman)

    assert resident.lapse == LapseEnum.lapsed and resident.contributions_blocked
    assert resident.blocks_at == fund.plan_expires_at + PLAN_GRACE
    assert not resident.can_contribute
    assert chairman.can_contribute


async def test_contribution_create_checks_plan():
    db = make_db()
    service = ContributionService(db=db)
    service.accounts.get_active_requisite = AsyncMock(return_value=SimpleNamespace(id=1, currency="tjs"))
    service.fund_repo.get = AsyncMock(return_value=expired_fund(10))
    service.member_repo.get_by_user = AsyncMock(return_value=make_member(role="resident"))
    service.plans.member_repo.count_active = AsyncMock(return_value=30)
    service.plans.member_repo.first_council_user_ids = AsyncMock(return_value=[2])
    payload = ContributionCreateIn(amount=100, requisite_id=1, receipt_image=RECEIPT, category="monthly_fee")

    with pytest.raises(HTTPException) as exc:
        await service.create(fund_id=1, user_id=1, payload=payload)

    assert exc.value.status_code == 403
    db.commit.assert_not_called()


# ─── Решение по заявке → уведомление ──────────────────────────────────────────


def plan_request(fund, status="pending"):
    return SimpleNamespace(
        id=1, fund_id=fund.id, fund=fund, plan="max", months=3, status=status, contact="+992", comment=None,
        admin_comment=None, requested_by=None, reviewed_at=None, created_at=NOW,
    )  # fmt: skip


async def test_reject_notifies_council_with_reason():
    db = make_db()
    service = PlanService(db=db)
    service.repo.get = AsyncMock(return_value=plan_request(make_fund(id=5)))

    await service.reject(request_id=1, admin_id=1, comment="Контакты не действительны")

    [notice] = added_notices(db)
    assert notice.fund_id == 5 and notice.kind == "plan_rejected"
    assert notice.details == {"plan": "max", "months": 3, "reason": "Контакты не действительны"}


async def test_approve_notifies_council():
    db = make_db()
    fund = make_fund(id=5)
    service = PlanService(db=db)
    service.repo.get = AsyncMock(return_value=plan_request(fund))
    service.fund_repo.get = AsyncMock(return_value=fund)

    await service.approve(request_id=1, admin_id=1, payload=PlanApproveIn())

    [notice] = added_notices(db)
    assert notice.kind == "plan_approved"
    assert notice.details["expires_at"] == fund.plan_expires_at.isoformat()


# ─── Окно уведомлений совета ──────────────────────────────────────────────────


def stored_notice(id: int, created_at: datetime, kind="admin_message"):
    return SimpleNamespace(id=id, kind=kind, text="Текст", details={}, created_at=created_at)


async def test_list_marks_unread_after_last_read():
    service = NoticeService(db=make_db())
    service.member_repo.get_by_user = AsyncMock(return_value=make_member(notices_read_at=NOW))
    service.repo.list = AsyncMock(
        return_value=[stored_notice(2, NOW + timedelta(hours=1)), stored_notice(1, NOW - timedelta(hours=1))]
    )
    service.repo.count_since = AsyncMock(return_value=1)

    result = await service.list(make_ctx(role=FundRoleEnum.chairman))

    assert [n.is_unread for n in result.items] == [True, False]
    assert result.unread == 1
    service.repo.count_since.assert_awaited_with(1, NOW)


async def test_mark_read_updates_member():
    db = make_db()
    member = make_member(notices_read_at=None)
    service = NoticeService(db=db)
    service.member_repo.get_by_user = AsyncMock(return_value=member)

    await service.mark_read(make_ctx(role=FundRoleEnum.admin))

    assert member.notices_read_at is not None
    db.commit.assert_awaited_once()


async def test_send_to_missing_fund_is_404():
    service = NoticeService(db=make_db())
    service.fund_repo.get = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service.send(fund_id=404, admin_id=1, text="Привет")
    assert exc.value.status_code == 404


async def test_send_creates_message_and_audit():
    db = make_db()
    service = NoticeService(db=db)
    service.fund_repo.get = AsyncMock(return_value=make_fund(id=3, name="Дом"))
    db.refresh = AsyncMock(side_effect=lambda notice: setattr(notice, "created_at", NOW) or setattr(notice, "id", 7))

    result = await service.send(fund_id=3, admin_id=1, text="  В фонде идёт модерация  ")

    [notice] = added_notices(db)
    assert notice.kind == "admin_message" and notice.text == "В фонде идёт модерация"
    assert result.fund_name == "Дом"
    actions = [call.args[0].action for call in db.add.call_args_list if hasattr(call.args[0], "action")]
    assert actions == ["notice.send"]


# ─── Фоновая проверка ─────────────────────────────────────────────────────────


async def test_check_plan_expiry_sends_each_stage_once_per_expiry():
    expiring = make_fund(id=1, plan="pro", plan_expires_at=NOW + timedelta(days=2))
    expired = expired_fund(2, id=2)
    lapsed_big = expired_fund(8, id=3)
    lapsed_small = expired_fund(8, id=4)

    db = make_db()
    service = NoticeService(db=db)
    service.repo.list_funds_by_expiry = AsyncMock(side_effect=[[expiring], [expired], [lapsed_big, lapsed_small]])
    service.member_repo.count_active = AsyncMock(side_effect=lambda fund_id: {2: 30, 3: 30, 4: 5}[fund_id])
    service.repo.add_once = AsyncMock(return_value=True)

    created = await service.check_plan_expiry(now=NOW)

    calls = [(c.args[0], c.kwargs["kind"]) for c in service.repo.add_once.await_args_list]
    assert calls == [
        (f"plan_expiring:1:{expiring.plan_expires_at.isoformat()}", "plan_expiring"),
        (f"plan_expired:2:{expired.plan_expires_at.isoformat()}", "plan_expired"),
        (f"plan_lapsed:3:{lapsed_big.plan_expires_at.isoformat()}", "plan_lapsed"),
    ]
    assert service.repo.add_once.await_args_list[1].kwargs["details"]["will_block"] is True
    assert created == 3
    db.commit.assert_awaited_once()

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.repositories.analytics_repo import effective_plan_sql
from app.services.analytics_service import AnalyticsService, month_periods
from tests.unit.helpers import make_db, make_fund, make_user


def make_service(**repo_methods) -> AnalyticsService:
    service = AnalyticsService(db=make_db())
    for name, value in repo_methods.items():
        setattr(service.repo, name, AsyncMock(return_value=value))
    return service


# ─── Месяцы ───────────────────────────────────────────────────────────────────


def test_month_periods_crosses_year():
    start, periods = month_periods(datetime(2026, 2, 15, tzinfo=timezone.utc), 4)
    assert periods == ["2025-11", "2025-12", "2026-01", "2026-02"]
    assert start == datetime(2025, 11, 1, tzinfo=timezone.utc)


def test_effective_plan_sql_treats_expired_as_free():
    sql = str(
        effective_plan_sql(datetime(2026, 1, 1, tzinfo=timezone.utc)).compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "funds.plan_expires_at IS NULL" in sql
    assert "ELSE 'free'" in sql


# ─── Обзор ────────────────────────────────────────────────────────────────────


def overview_service(**overrides) -> AnalyticsService:
    now = datetime.now(timezone.utc)
    _, periods = month_periods(now, 3)
    fields = dict(
        count_plan_requests_by_status={"pending": 2, "approved": 5},
        count_users=7,
        count_active_users=3,
        count_funds=2,
        count_active_funds=1,
        count_members=4,
        count_contributions=1,
        verification_stats={"verified": 5, "unverified": 2, "google": 1, "sms": 4},
        new_users_by_month={periods[0]: 2, periods[2]: 3},
        new_funds_by_month={periods[1]: 1},
        contributions_by_month=[(periods[2], "tjs", 500), (periods[2], "usd", 20)],
        expenses_by_month=[(periods[2], "tjs", 200), (periods[0], "tjs", 50)],
        contributions_by_currency={"tjs": 500, "usd": 20},
        expenses_by_currency={"tjs": 250},
    )
    fields.update(overrides)
    return make_service(**fields)


async def test_overview_growth_is_cumulative_from_before_window():
    service = overview_service()
    # count_users(until=start) — пользователи до окна; остальные вызовы — сводка
    service.repo.count_users = AsyncMock(side_effect=lambda since=None, until=None: 10 if until else 20)
    service.repo.count_funds = AsyncMock(side_effect=lambda since=None, until=None: 1 if until else 2)

    result = await service.overview(months=3)

    assert [p.users for p in result.growth] == [2, 0, 3]
    assert [p.users_total for p in result.growth] == [12, 12, 15]
    assert [p.funds_total for p in result.growth] == [1, 2, 2]
    assert result.totals.pending_plan_requests == 2
    assert result.verification.google == 1


async def test_overview_money_keeps_currencies_apart():
    result = await overview_service().overview(months=3)

    # Месяцы по порядку, внутри месяца — валюты по алфавиту; разные валюты не складываются
    assert [(p.currency, p.contributions, p.expenses) for p in result.money] == [
        ("tjs", 0, 50),
        ("tjs", 500, 200),
        ("usd", 20, 0),
    ]
    assert [(c.currency, c.contributions, c.expenses) for c in result.currencies] == [
        ("tjs", 500, 250),
        ("usd", 20, 0),
    ]


# ─── Тарифы ───────────────────────────────────────────────────────────────────


async def test_plans_fills_every_plan_and_month():
    now = datetime.now(timezone.utc)
    _, periods = month_periods(now, 2)
    expiring = make_fund(id=3, name="Дом", plan="pro", plan_expires_at=now + timedelta(days=5))
    service = make_service(
        plan_distribution={"free": 4, "pro": 1},
        revenue_by_month={periods[1]: (398, 1)},
        count_plan_requests_by_status={"approved": 1, "rejected": 2},
        expiring_funds=[expiring],
        revenue_total=398,
        mrr=199,
    )

    result = await service.plans(months=2)

    assert {d.plan.value: d.funds for d in result.distribution} == {"free": 4, "pro": 1, "max": 0, "individual": 0}
    assert [(r.amount_tjs, r.approvals) for r in result.revenue] == [(0, 0), (398, 1)]
    assert result.requests.pending == 0 and result.requests.rejected == 2
    assert result.expiring[0].id == 3
    assert result.mrr_tjs == 199


# ─── Фонды ────────────────────────────────────────────────────────────────────


def health_row(fund, last_activity_at, effective_plan="free"):
    return SimpleNamespace(
        Fund=fund,
        effective_plan=effective_plan,
        members_active=3,
        pending_members=1,
        pending_contributions=2,
        stale_contributions=1,
        contributions_30d=None,
        last_activity_at=last_activity_at,
    )


async def test_funds_marks_inactive_and_hides_expired_plan_date():
    now = datetime.now(timezone.utc)
    expired = make_fund(id=1, address=None, created_at=now, plan="pro", plan_expires_at=now - timedelta(days=1))
    active = make_fund(id=2, address=None, created_at=now)
    service = make_service(
        list_fund_health=([health_row(expired, None), health_row(active, now - timedelta(days=2))], 2)
    )

    result = await service.funds(query="  ", sort="activity")

    assert result.total == 2
    assert [f.inactive for f in result.items] == [True, False]
    # Истёкший pro — действует free, дата окончания не показывается, лимит — как у free
    assert result.items[0].plan_expires_at is None
    assert result.items[0].member_limit == 10
    assert result.items[0].contributions_30d == 0
    # Пустой поиск не уходит в SQL
    assert service.repo.list_fund_health.await_args.kwargs["query"] is None


# ─── Пользователи ─────────────────────────────────────────────────────────────


async def test_users_parses_providers():
    user = make_user(id=5)
    row = SimpleNamespace(User=user, providers="google,telegram,google", funds_count=2, last_seen_at=None)
    service = make_service(list_users=([row], 1))

    result = await service.users(query="Али", filter="unverified")

    assert result.items[0].providers == ["google", "telegram"]
    assert result.items[0].funds_count == 2
    assert service.repo.list_users.await_args.kwargs == dict(query="Али", filter="unverified", skip=0, limit=50)


async def test_user_detail_includes_memberships():
    user = make_user(id=5)
    row = SimpleNamespace(User=user, providers=None, funds_count=1, last_seen_at=None)
    member = SimpleNamespace(fund_id=1, role="chairman", status="active", address_unit="кв. 3", joined_at=None)
    service = make_service(
        get_user_row=row,
        list_memberships=[SimpleNamespace(FundMember=member, fund_name="Дом")],
        count_active_sessions=2,
    )

    result = await service.user(user_id=5)

    assert result.providers == []
    assert result.memberships[0].fund_name == "Дом"
    assert result.sessions_active == 2


async def test_user_detail_not_found():
    service = make_service(get_user_row=None)
    with pytest.raises(HTTPException) as error:
        await service.user(user_id=404)
    assert error.value.status_code == 404


# ─── Журнал ───────────────────────────────────────────────────────────────────


async def test_audit_adds_fund_and_actor_names():
    event = SimpleNamespace(
        id=1,
        fund_id=None,
        action="user.delete",
        entity="user",
        entity_id=9,
        details=None,
        actor_id=9,
        created_at=datetime.now(timezone.utc),
    )
    service = make_service(list_audit=[SimpleNamespace(AuditEvent=event, fund_name=None, actor_name="Удалённый")])

    result = await service.audit(entity="user")

    assert result[0].details == {}
    assert result[0].actor_name == "Удалённый"
    assert service.repo.list_audit.await_args.kwargs["entity"] == "user"

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import member_limit
from app.enums import ContributionStatusEnum, MemberStatusEnum, PlanEnum, PlanRequestStatusEnum
from app.repositories.analytics_repo import AnalyticsRepository
from app.schemas.analytics import (
    AuditEventOutAdmin,
    CurrencyTotalOut,
    ExpiringFundOut,
    FundHealthListOut,
    FundHealthOut,
    GrowthPointOut,
    MoneyPointOut,
    PlanRequestStatsOut,
    PlanShareOut,
    PlatformOverviewOut,
    PlatformPlansOut,
    PlatformTotalsOut,
    RevenuePointOut,
    UserDetailOutAdmin,
    UserListOutAdmin,
    UserMembershipOut,
    UserOutAdmin,
    VerificationStatsOut,
)

# Окно «активности» и «новых» — 30 дней
ACTIVE_WINDOW = timedelta(days=30)
# Чек ждёт совета дольше — фонд в зоне внимания
STALE_RECEIPT = timedelta(days=3)
# Тарифы, которые истекают в ближайшие дни
EXPIRING_WINDOW = timedelta(days=14)


def month_periods(now: datetime, months: int) -> tuple[datetime, list[str]]:
    """Начало первого месяца окна и список месяцев YYYY-MM от старого к текущему."""
    year, month = now.year, now.month
    periods = []
    for _ in range(months):
        periods.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    periods.reverse()
    first_year, first_month = map(int, periods[0].split("-"))
    return datetime(first_year, first_month, 1, tzinfo=timezone.utc), periods


class AnalyticsService:
    """Аналитика платформы для админа: сводка, тарифы, здоровье фондов, пользователи, журнал. Только чтение."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AnalyticsRepository(db=db)

    # ─── Обзор ─────────────────────────────────────────────────────────────────

    async def overview(self, months: int = 12) -> PlatformOverviewOut:
        now = datetime.now(timezone.utc)
        since = now - ACTIVE_WINDOW
        start, periods = month_periods(now, months)

        requests = await self.repo.count_plan_requests_by_status()
        totals = PlatformTotalsOut(
            users_total=await self.repo.count_users(),
            users_new_30d=await self.repo.count_users(since=since),
            users_active_7d=await self.repo.count_active_users(now - timedelta(days=7)),
            users_active_30d=await self.repo.count_active_users(since),
            funds_total=await self.repo.count_funds(),
            funds_new_30d=await self.repo.count_funds(since=since),
            funds_active_30d=await self.repo.count_active_funds(since),
            members_active=await self.repo.count_members(MemberStatusEnum.active.value),
            pending_contributions=await self.repo.count_contributions(ContributionStatusEnum.pending.value),
            pending_members=await self.repo.count_members(MemberStatusEnum.pending.value),
            pending_plan_requests=requests.get(PlanRequestStatusEnum.pending.value, 0),
        )

        # Рост: новые за месяц + накопительный итог от числа созданных до окна
        new_users = await self.repo.new_users_by_month(start)
        new_funds = await self.repo.new_funds_by_month(start)
        users_total = await self.repo.count_users(until=start)
        funds_total = await self.repo.count_funds(until=start)
        growth = []
        for period in periods:
            users_total += new_users.get(period, 0)
            funds_total += new_funds.get(period, 0)
            growth.append(
                GrowthPointOut(
                    period=period,
                    users=new_users.get(period, 0),
                    funds=new_funds.get(period, 0),
                    users_total=users_total,
                    funds_total=funds_total,
                )
            )

        # Деньги по месяцам и валютам — суммы в разных валютах не складываются
        money: dict[tuple[str, str], list[int]] = {}
        for period, currency, amount in await self.repo.contributions_by_month(start):
            money.setdefault((period, currency), [0, 0])[0] = amount
        for period, currency, amount in await self.repo.expenses_by_month(start):
            money.setdefault((period, currency), [0, 0])[1] = amount
        order = {p: i for i, p in enumerate(periods)}
        money_points = [
            MoneyPointOut(period=p, currency=c, contributions=v[0], expenses=v[1])
            for (p, c), v in sorted(money.items(), key=lambda item: (order.get(item[0][0], -1), item[0][1]))
        ]

        contributions = await self.repo.contributions_by_currency()
        expenses = await self.repo.expenses_by_currency()
        currencies = [
            CurrencyTotalOut(currency=c, contributions=contributions.get(c, 0), expenses=expenses.get(c, 0))
            for c in sorted(set(contributions) | set(expenses))
        ]

        return PlatformOverviewOut(
            totals=totals,
            verification=VerificationStatsOut(**await self.repo.verification_stats()),
            growth=growth,
            money=money_points,
            currencies=currencies,
        )

    # ─── Тарифы и выручка ──────────────────────────────────────────────────────

    async def plans(self, months: int = 12) -> PlatformPlansOut:
        now = datetime.now(timezone.utc)
        start, periods = month_periods(now, months)

        distribution = await self.repo.plan_distribution(now)
        revenue = await self.repo.revenue_by_month(start)
        requests = await self.repo.count_plan_requests_by_status()
        expiring = await self.repo.expiring_funds(now, now + EXPIRING_WINDOW)

        return PlatformPlansOut(
            distribution=[PlanShareOut(plan=plan, funds=distribution.get(plan.value, 0)) for plan in PlanEnum],
            revenue=[
                RevenuePointOut(period=p, amount_tjs=revenue.get(p, (0, 0))[0], approvals=revenue.get(p, (0, 0))[1])
                for p in periods
            ],
            revenue_total_tjs=await self.repo.revenue_total(),
            revenue_30d_tjs=await self.repo.revenue_total(since=now - ACTIVE_WINDOW),
            mrr_tjs=await self.repo.mrr(now),
            requests=PlanRequestStatsOut(**{s.value: requests.get(s.value, 0) for s in PlanRequestStatusEnum}),
            expiring=[
                ExpiringFundOut(id=f.id, name=f.name, code=f.code, plan=f.plan, plan_expires_at=f.plan_expires_at)
                for f in expiring
            ],
        )

    # ─── Фонды ─────────────────────────────────────────────────────────────────

    async def funds(
        self,
        query: str | None = None,
        plan: PlanEnum | None = None,
        inactive_only: bool = False,
        sort: str = "created",
        skip: int = 0,
        limit: int = 50,
    ) -> FundHealthListOut:
        now = datetime.now(timezone.utc)
        since = now - ACTIVE_WINDOW
        rows, total = await self.repo.list_fund_health(
            now=now,
            since=since,
            stale_before=now - STALE_RECEIPT,
            query=(query or "").strip() or None,
            plan=plan.value if plan else None,
            inactive_only=inactive_only,
            sort=sort,
            skip=skip,
            limit=limit,
        )
        items = [
            FundHealthOut(
                id=row.Fund.id,
                name=row.Fund.name,
                code=row.Fund.code,
                address=row.Fund.address,
                effective_plan=row.effective_plan,
                plan_expires_at=row.Fund.plan_expires_at if row.effective_plan != PlanEnum.free.value else None,
                members_active=row.members_active or 0,
                member_limit=member_limit(row.Fund),
                pending_members=row.pending_members or 0,
                pending_contributions=row.pending_contributions or 0,
                stale_contributions=row.stale_contributions or 0,
                contributions_30d=row.contributions_30d or 0,
                last_activity_at=row.last_activity_at,
                inactive=row.last_activity_at is None or row.last_activity_at < since,
                created_at=row.Fund.created_at,
            )
            for row in rows
        ]
        return FundHealthListOut(items=items, total=total)

    # ─── Пользователи ──────────────────────────────────────────────────────────

    async def users(
        self, query: str | None = None, filter: str = "all", skip: int = 0, limit: int = 50
    ) -> UserListOutAdmin:
        rows, total = await self.repo.list_users(
            query=(query or "").strip() or None, filter=filter, skip=skip, limit=limit
        )
        return UserListOutAdmin(items=[self._user_out(row) for row in rows], total=total)

    async def user(self, user_id: int) -> UserDetailOutAdmin:
        row = await self.repo.get_user_row(user_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        memberships = [
            UserMembershipOut(
                fund_id=m.FundMember.fund_id,
                fund_name=m.fund_name,
                role=m.FundMember.role,
                status=m.FundMember.status,
                address_unit=m.FundMember.address_unit,
                joined_at=m.FundMember.joined_at,
            )
            for m in await self.repo.list_memberships(user_id)
        ]
        return UserDetailOutAdmin(
            **self._user_out(row).model_dump(),
            memberships=memberships,
            sessions_active=await self.repo.count_active_sessions(user_id, datetime.now(timezone.utc)),
        )

    # ─── Журнал ────────────────────────────────────────────────────────────────

    async def audit(
        self,
        fund_id: int | None = None,
        actor_id: int | None = None,
        entity: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditEventOutAdmin]:
        rows = await self.repo.list_audit(fund_id=fund_id, actor_id=actor_id, entity=entity, skip=skip, limit=limit)
        return [
            AuditEventOutAdmin(
                id=row.AuditEvent.id,
                fund_id=row.AuditEvent.fund_id,
                fund_name=row.fund_name,
                action=row.AuditEvent.action,
                entity=row.AuditEvent.entity,
                entity_id=row.AuditEvent.entity_id,
                details=row.AuditEvent.details or {},
                actor_id=row.AuditEvent.actor_id,
                actor_name=row.actor_name,
                created_at=row.AuditEvent.created_at,
            )
            for row in rows
        ]

    # ─── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _user_out(row) -> UserOutAdmin:
        user = row.User
        return UserOutAdmin(
            id=user.id,
            full_name=user.full_name,
            phone=user.phone,
            email=user.email,
            is_platform_admin=user.is_platform_admin,
            verified_at=user.verified_at,
            deleted_at=user.deleted_at,
            providers=sorted(set(row.providers.split(","))) if row.providers else [],
            funds_count=row.funds_count or 0,
            last_seen_at=row.last_seen_at,
            created_at=user.created_at,
        )

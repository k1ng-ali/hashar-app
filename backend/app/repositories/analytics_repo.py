"""
Агрегаты по всей платформе для админа платформы.

Всё считается в SQL (count / sum / group by) — строки взносов, расходов и пользователей
в память не загружаются. Месяц — date_trunc('month') в часовом поясе сессии БД.
"""

from datetime import datetime

from sqlalchemy import Integer, String, and_, case, func, literal, or_, select, union_all
from sqlalchemy.sql.elements import ColumnElement

from app.enums import ContributionStatusEnum, MemberStatusEnum, PlanEnum
from app.models.audit_event import AuditEvent
from app.models.auth_session import AuthSession
from app.models.contribution import Contribution
from app.models.expense import Expense
from app.models.fund import Fund
from app.models.member import FundMember
from app.models.plan_request import PlanRequest
from app.models.user import User, UserAuthProvider
from app.models.verification import VerificationCode
from app.repositories.base_repo import BaseRepository, like_pattern

ACTIVE = MemberStatusEnum.active.value
PENDING_MEMBER = MemberStatusEnum.pending.value
PENDING = ContributionStatusEnum.pending.value
APPROVED = ContributionStatusEnum.approved.value
FREE = PlanEnum.free.value


def month_of(column) -> ColumnElement[str]:
    return func.to_char(func.date_trunc("month", column), "YYYY-MM")


def effective_plan_sql(now: datetime) -> ColumnElement[str]:
    """Действующий тариф фонда (как core/plans.effective_plan): истёкший платный — это free."""
    return case(
        (
            and_(Fund.plan != FREE, or_(Fund.plan_expires_at.is_(None), Fund.plan_expires_at > now)),
            Fund.plan,
        ),
        else_=literal(FREE),
    )


def user_stats_columns() -> tuple:
    """Способы входа (через запятую), число фондов, где участник активен, и последний вход."""
    providers = (
        select(func.string_agg(UserAuthProvider.provider, literal(",", String)))
        .where(UserAuthProvider.user_id == User.id)
        .scalar_subquery()
    )
    funds_count = (
        select(func.count(FundMember.id))
        .where(FundMember.user_id == User.id, FundMember.status == ACTIVE)
        .scalar_subquery()
    )
    last_seen = select(func.max(AuthSession.last_used_at)).where(AuthSession.user_id == User.id).scalar_subquery()
    return providers.label("providers"), funds_count.label("funds_count"), last_seen.label("last_seen_at")


class AnalyticsRepository(BaseRepository):

    async def _scalar(self, stmt) -> int:
        return int((await self.db.execute(stmt)).scalar() or 0)

    # ─── Обзор ─────────────────────────────────────────────────────────────────

    async def count_users(self, since: datetime | None = None, until: datetime | None = None) -> int:
        stmt = select(func.count(User.id)).where(User.deleted_at.is_(None))
        if since is not None:
            stmt = stmt.where(User.created_at >= since)
        if until is not None:
            stmt = stmt.where(User.created_at < until)
        return await self._scalar(stmt)

    async def count_funds(self, since: datetime | None = None, until: datetime | None = None) -> int:
        stmt = select(func.count(Fund.id))
        if since is not None:
            stmt = stmt.where(Fund.created_at >= since)
        if until is not None:
            stmt = stmt.where(Fund.created_at < until)
        return await self._scalar(stmt)

    async def count_active_users(self, since: datetime) -> int:
        """Пользователи, у которых сессия использовалась после since (вход или обновление токена)."""
        return await self._scalar(
            select(func.count(func.distinct(AuthSession.user_id)))
            .join(User, User.id == AuthSession.user_id)
            .where(AuthSession.last_used_at >= since, User.deleted_at.is_(None))
        )

    async def count_active_funds(self, since: datetime) -> int:
        """Фонды, где после since был взнос или расход."""
        activity = union_all(
            select(Contribution.fund_id.label("fund_id")).where(Contribution.created_at >= since),
            select(Expense.fund_id.label("fund_id")).where(Expense.created_at >= since, Expense.deleted_at.is_(None)),
        ).subquery()
        return await self._scalar(select(func.count(func.distinct(activity.c.fund_id))))

    async def count_members(self, status: str) -> int:
        return await self._scalar(select(func.count(FundMember.id)).where(FundMember.status == status))

    async def count_contributions(self, status: str) -> int:
        return await self._scalar(select(func.count(Contribution.id)).where(Contribution.status == status))

    async def count_plan_requests_by_status(self) -> dict[str, int]:
        result = await self.db.execute(
            select(PlanRequest.status, func.count(PlanRequest.id)).group_by(PlanRequest.status)
        )
        return {status: int(count) for status, count in result.all()}

    async def verification_stats(self) -> dict[str, int]:
        has_google = (
            select(UserAuthProvider.id)
            .where(UserAuthProvider.user_id == User.id, UserAuthProvider.provider == "google")
            .exists()
        )
        has_sms = (
            select(VerificationCode.id)
            .where(VerificationCode.user_id == User.id, VerificationCode.consumed_at.is_not(None))
            .exists()
        )
        row = (
            await self.db.execute(
                select(
                    func.count(User.id).filter(User.verified_at.is_not(None)),
                    func.count(User.id).filter(User.verified_at.is_(None)),
                    func.count(User.id).filter(has_google),
                    func.count(User.id).filter(has_sms),
                ).where(User.deleted_at.is_(None))
            )
        ).one()
        return {"verified": row[0], "unverified": row[1], "google": row[2], "sms": row[3]}

    async def new_users_by_month(self, since: datetime) -> dict[str, int]:
        period = month_of(User.created_at)
        result = await self.db.execute(
            select(period, func.count(User.id))
            .where(User.created_at >= since, User.deleted_at.is_(None))
            .group_by(period)
        )
        return {p: int(c) for p, c in result.all()}

    async def new_funds_by_month(self, since: datetime) -> dict[str, int]:
        period = month_of(Fund.created_at)
        result = await self.db.execute(
            select(period, func.count(Fund.id)).where(Fund.created_at >= since).group_by(period)
        )
        return {p: int(c) for p, c in result.all()}

    async def contributions_by_month(self, since: datetime) -> list[tuple[str, str, int]]:
        """Одобренные взносы: (месяц, валюта оплаты, сумма)."""
        period = month_of(Contribution.created_at)
        result = await self.db.execute(
            select(period, Contribution.currency, func.sum(Contribution.amount))
            .where(Contribution.status == APPROVED, Contribution.created_at >= since)
            .group_by(period, Contribution.currency)
        )
        return [(p, c, int(s or 0)) for p, c, s in result.all()]

    async def expenses_by_month(self, since: datetime) -> list[tuple[str, str, int]]:
        period = month_of(Expense.created_at)
        result = await self.db.execute(
            select(period, Expense.currency, func.sum(Expense.amount))
            .where(Expense.deleted_at.is_(None), Expense.created_at >= since)
            .group_by(period, Expense.currency)
        )
        return [(p, c, int(s or 0)) for p, c, s in result.all()]

    async def contributions_by_currency(self) -> dict[str, int]:
        result = await self.db.execute(
            select(Contribution.currency, func.sum(Contribution.amount))
            .where(Contribution.status == APPROVED)
            .group_by(Contribution.currency)
        )
        return {c: int(s or 0) for c, s in result.all()}

    async def expenses_by_currency(self) -> dict[str, int]:
        result = await self.db.execute(
            select(Expense.currency, func.sum(Expense.amount))
            .where(Expense.deleted_at.is_(None))
            .group_by(Expense.currency)
        )
        return {c: int(s or 0) for c, s in result.all()}

    # ─── Тарифы и выручка ──────────────────────────────────────────────────────

    async def plan_distribution(self, now: datetime) -> dict[str, int]:
        plan = effective_plan_sql(now)
        result = await self.db.execute(select(plan, func.count(Fund.id)).group_by(plan))
        return {p: int(c) for p, c in result.all()}

    async def mrr(self, now: datetime) -> int:
        """Сумма месячных цен действующих платных тарифов, TJS."""
        return await self._scalar(
            select(func.sum(func.coalesce(Fund.plan_price, 0))).where(effective_plan_sql(now) != FREE)
        )

    @staticmethod
    def _payment_tjs() -> ColumnElement[int]:
        """Оплата по заявке из снимка в журнале (plan.approve); в старых записях нет total — цена × месяцы."""
        price = func.coalesce(AuditEvent.details["price"].astext.cast(Integer), 0)
        months = func.coalesce(AuditEvent.details["months"].astext.cast(Integer), 0)
        return func.coalesce(AuditEvent.details["total"].astext.cast(Integer), price * months)

    async def revenue_by_month(self, since: datetime) -> dict[str, tuple[int, int]]:
        """Месяц → (выручка TJS, число одобренных заявок)."""
        period = month_of(AuditEvent.created_at)
        result = await self.db.execute(
            select(period, func.sum(self._payment_tjs()), func.count(AuditEvent.id))
            .where(AuditEvent.action == "plan.approve", AuditEvent.created_at >= since)
            .group_by(period)
        )
        return {p: (int(s or 0), int(c)) for p, s, c in result.all()}

    async def revenue_total(self, since: datetime | None = None) -> int:
        stmt = select(func.sum(self._payment_tjs())).where(AuditEvent.action == "plan.approve")
        if since is not None:
            stmt = stmt.where(AuditEvent.created_at >= since)
        return await self._scalar(stmt)

    async def expiring_funds(self, now: datetime, until: datetime, limit: int = 20) -> list[Fund]:
        result = await self.db.execute(
            select(Fund)
            .where(Fund.plan != FREE, Fund.plan_expires_at > now, Fund.plan_expires_at <= until)
            .order_by(Fund.plan_expires_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ─── Фонды ─────────────────────────────────────────────────────────────────

    async def list_fund_health(
        self,
        now: datetime,
        since: datetime,
        stale_before: datetime,
        query: str | None = None,
        plan: str | None = None,
        inactive_only: bool = False,
        sort: str = "created",
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list, int]:
        """Фонды со счётчиками — коррелированные подзапросы считаются только для страницы."""
        members_active = (
            select(func.count(FundMember.id))
            .where(FundMember.fund_id == Fund.id, FundMember.status == ACTIVE)
            .scalar_subquery()
        )
        pending_members = (
            select(func.count(FundMember.id))
            .where(FundMember.fund_id == Fund.id, FundMember.status == PENDING_MEMBER)
            .scalar_subquery()
        )
        pending_contributions = (
            select(func.count(Contribution.id))
            .where(Contribution.fund_id == Fund.id, Contribution.status == PENDING)
            .scalar_subquery()
        )
        stale_contributions = (
            select(func.count(Contribution.id))
            .where(
                Contribution.fund_id == Fund.id,
                Contribution.status == PENDING,
                Contribution.created_at < stale_before,
            )
            .scalar_subquery()
        )
        contributions_30d = (
            select(func.count(Contribution.id))
            .where(Contribution.fund_id == Fund.id, Contribution.created_at >= since)
            .scalar_subquery()
        )
        last_contribution = (
            select(func.max(Contribution.created_at)).where(Contribution.fund_id == Fund.id).scalar_subquery()
        )
        last_expense = (
            select(func.max(Expense.created_at))
            .where(Expense.fund_id == Fund.id, Expense.deleted_at.is_(None))
            .scalar_subquery()
        )
        # greatest() в PostgreSQL пропускает NULL
        last_activity = func.greatest(last_contribution, last_expense)
        effective = effective_plan_sql(now)

        filters = []
        if query:
            pattern = like_pattern(query)
            filters.append(
                or_(
                    Fund.name.ilike(pattern, escape="\\"),
                    Fund.code.ilike(pattern, escape="\\"),
                    Fund.address.ilike(pattern, escape="\\"),
                )
            )
        if plan:
            filters.append(effective == plan)
        if inactive_only:
            filters.append(or_(last_activity.is_(None), last_activity < since))

        order = {
            "members": members_active.desc(),
            "activity": last_activity.desc().nulls_last(),
            "pending": (pending_contributions + pending_members).desc(),
        }.get(sort, Fund.created_at.desc())

        stmt = (
            select(
                Fund,
                effective.label("effective_plan"),
                members_active.label("members_active"),
                pending_members.label("pending_members"),
                pending_contributions.label("pending_contributions"),
                stale_contributions.label("stale_contributions"),
                contributions_30d.label("contributions_30d"),
                last_activity.label("last_activity_at"),
            )
            .where(*filters)
            .order_by(order, Fund.id.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = list((await self.db.execute(stmt)).all())
        total = await self._scalar(select(func.count(Fund.id)).where(*filters))
        return rows, total

    # ─── Пользователи ──────────────────────────────────────────────────────────

    async def list_users(self, query: str | None = None, filter: str = "all", skip: int = 0, limit: int = 50):

        filters = []
        if query:
            pattern = like_pattern(query)
            filters.append(
                or_(
                    User.full_name.ilike(pattern, escape="\\"),
                    User.phone.ilike(pattern, escape="\\"),
                    User.email.ilike(pattern, escape="\\"),
                )
            )
        if filter == "deleted":
            filters.append(User.deleted_at.is_not(None))
        else:
            filters.append(User.deleted_at.is_(None))
            if filter == "unverified":
                filters.append(User.verified_at.is_(None))
            elif filter == "admins":
                filters.append(User.is_platform_admin.is_(True))

        stmt = (
            select(User, *user_stats_columns())
            .where(*filters)
            .order_by(User.created_at.desc(), User.id.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = list((await self.db.execute(stmt)).all())
        total = await self._scalar(select(func.count(User.id)).where(*filters))
        return rows, total

    async def get_user_row(self, user_id: int):
        result = await self.db.execute(select(User, *user_stats_columns()).where(User.id == user_id))
        return result.one_or_none()

    async def list_memberships(self, user_id: int) -> list:
        result = await self.db.execute(
            select(FundMember, Fund.name.label("fund_name"))
            .join(Fund, Fund.id == FundMember.fund_id)
            .where(FundMember.user_id == user_id)
            .order_by(FundMember.created_at.desc())
        )
        return list(result.all())

    async def count_active_sessions(self, user_id: int, now: datetime) -> int:
        return await self._scalar(
            select(func.count(AuthSession.id)).where(
                AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None), AuthSession.expires_at > now
            )
        )

    # ─── Журнал ────────────────────────────────────────────────────────────────

    async def list_audit(
        self,
        fund_id: int | None = None,
        actor_id: int | None = None,
        entity: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list:
        """События всей платформы с названием фонда и именем автора — новые первыми."""
        stmt = (
            select(AuditEvent, Fund.name.label("fund_name"), User.full_name.label("actor_name"))
            .outerjoin(Fund, Fund.id == AuditEvent.fund_id)
            .outerjoin(User, User.id == AuditEvent.actor_id)
        )
        if fund_id is not None:
            stmt = stmt.where(AuditEvent.fund_id == fund_id)
        if actor_id is not None:
            stmt = stmt.where(AuditEvent.actor_id == actor_id)
        if entity:
            stmt = stmt.where(AuditEvent.entity == entity)
        result = await self.db.execute(
            stmt.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).offset(skip).limit(limit)
        )
        return list(result.all())

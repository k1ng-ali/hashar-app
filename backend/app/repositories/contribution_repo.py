from datetime import datetime

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import selectinload

from app.enums import ContributionCategoryEnum, ContributionStatusEnum
from app.models.contribution import Contribution
from app.repositories.base_repo import BaseRepository

APPROVED = ContributionStatusEnum.approved.value
PENDING = ContributionStatusEnum.pending.value
MONTHLY_FEE = ContributionCategoryEnum.monthly_fee.value


def _with_relations(stmt):
    return stmt.options(
        selectinload(Contribution.user),
        selectinload(Contribution.reviewed_by),
        selectinload(Contribution.target_fund),
    )


class ContributionRepository(BaseRepository):

    # ─── Чтение ────────────────────────────────────────────────────────────────

    async def get(self, fund_id: int, contribution_id: int, for_update: bool = False) -> Contribution | None:
        stmt = _with_relations(
            select(Contribution).where(Contribution.id == contribution_id, Contribution.fund_id == fund_id)
        )
        # populate_existing — чтобы связи догрузились и у объекта, уже лежащего в сессии
        stmt = stmt.execution_options(populate_existing=True)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        fund_id: int,
        user_id: int | None = None,
        status: str | None = None,
        category: str | None = None,
        currency: str | None = None,
        target_fund_id: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Contribution]:
        stmt = select(Contribution).where(Contribution.fund_id == fund_id)
        if user_id is not None:
            stmt = stmt.where(Contribution.user_id == user_id)
        if status:
            stmt = stmt.where(Contribution.status == status)
        if category:
            stmt = stmt.where(Contribution.category == category)
        if currency:
            stmt = stmt.where(Contribution.currency == currency)
        if target_fund_id is not None:
            stmt = stmt.where(Contribution.target_fund_id == target_fund_id)

        stmt = _with_relations(stmt.order_by(Contribution.created_at.desc()).offset(skip).limit(limit))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ─── Агрегаты ──────────────────────────────────────────────────────────────

    async def monthly_sums_by_user(
        self,
        fund_id: int,
        currency: str,
        user_ids: list[int] | None = None,
    ) -> dict[int, dict[str, int]]:
        """{user_id: {"approved": сумма, "pending": сумма}} ежемесячных взносов в базовой валюте."""
        stmt = (
            select(Contribution.user_id, Contribution.status, func.sum(Contribution.amount))
            .where(
                Contribution.fund_id == fund_id,
                Contribution.currency == currency,
                Contribution.category == MONTHLY_FEE,
                Contribution.status.in_([APPROVED, PENDING]),
            )
            .group_by(Contribution.user_id, Contribution.status)
        )
        if user_ids is not None:
            stmt = stmt.where(Contribution.user_id.in_(user_ids))

        result = await self.db.execute(stmt)
        sums: dict[int, dict[str, int]] = {}
        for user_id, status, total in result.all():
            sums.setdefault(user_id, {APPROVED: 0, PENDING: 0})[status] = int(total or 0)
        return sums

    async def approved_sums_by_currency(
        self,
        fund_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict[str, int]:
        stmt = select(Contribution.currency, func.sum(Contribution.amount)).where(
            Contribution.fund_id == fund_id, Contribution.status == APPROVED
        )
        if start:
            stmt = stmt.where(Contribution.created_at >= start)
        if end:
            stmt = stmt.where(Contribution.created_at < end)
        result = await self.db.execute(stmt.group_by(Contribution.currency))
        return {currency: int(total or 0) for currency, total in result.all()}

    async def count_pending(self, fund_id: int) -> int:
        result = await self.db.execute(
            select(func.count(Contribution.id)).where(Contribution.fund_id == fund_id, Contribution.status == PENDING)
        )
        return result.scalar() or 0

    async def collected_by_target_funds(self, fund_id: int) -> dict[int, tuple[int, int]]:
        """{target_fund_id: (собрано, число уникальных участников)} по одобренным взносам."""
        result = await self.db.execute(
            select(
                Contribution.target_fund_id,
                func.sum(Contribution.amount),
                func.count(distinct(Contribution.user_id)),
            )
            .where(
                Contribution.fund_id == fund_id,
                Contribution.status == APPROVED,
                Contribution.target_fund_id.is_not(None),
            )
            .group_by(Contribution.target_fund_id)
        )
        return {target_id: (int(total or 0), int(users)) for target_id, total, users in result.all()}

    async def approved_monthly_sums(
        self,
        fund_id: int,
        currency: str | None = None,
        target_fund_id: int | None = None,
    ) -> dict[str, int]:
        """{"YYYY-MM": сумма} одобренных взносов."""
        period = func.to_char(Contribution.created_at, "YYYY-MM")
        stmt = select(period, func.sum(Contribution.amount)).where(
            Contribution.fund_id == fund_id, Contribution.status == APPROVED
        )
        if currency:
            stmt = stmt.where(Contribution.currency == currency)
        if target_fund_id is not None:
            stmt = stmt.where(Contribution.target_fund_id == target_fund_id)

        result = await self.db.execute(stmt.group_by(period))
        return {p: int(total or 0) for p, total in result.all()}

    # ─── Запись ────────────────────────────────────────────────────────────────

    async def create(self, **fields) -> Contribution:
        contribution = Contribution(**fields)
        self.db.add(contribution)
        await self.db.flush()
        # Перечитываем вместе со связями (user, target_fund) для ответа
        return await self.get(contribution.fund_id, contribution.id)

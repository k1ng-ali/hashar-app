# Метод list() в классе затеняет встроенный list в аннотациях ниже (Python 3.12) — аннотации отложенные
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.finance import current_period, shift_period
from app.enums import ContributionStatusEnum
from app.models.target_fund import TargetFund
from app.repositories.audit_repo import AuditRepository
from app.repositories.contribution_repo import ContributionFilters, ContributionRepository
from app.repositories.expense_repo import ExpenseRepository
from app.repositories.target_fund_repo import TargetFundRepository
from app.schemas.member import FundContext
from app.schemas.target_fund import (
    MonthAmountOut,
    TargetFundCreateIn,
    TargetFundDetailOut,
    TargetFundOut,
    TargetFundUpdateIn,
)
from app.services.account_service import AccountService
from app.services.contribution_service import contribution_out

# Сколько последних месяцев показывать на графике динамики сбора
CHART_MONTHS = 6


def _target_fund_out(target: TargetFund, collected: int, contributors: int) -> TargetFundOut:
    goal = target.target_amount or 1
    return TargetFundOut(
        id=target.id,
        title=target.title,
        description=target.description,
        target_amount=target.target_amount,
        currency=target.currency,
        category=target.category,
        is_active=target.is_active,
        collected_amount=collected,
        remaining_amount=max(0, target.target_amount - collected),
        percent=min(100, round(collected / goal * 100)),
        contributors_count=contributors,
        created_at=target.created_at,
    )


class TargetFundService:
    """Целевые сборы внутри фонда (шлагбаум, озеленение...)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TargetFundRepository(db=db)
        self.contribution_repo = ContributionRepository(db=db)
        self.expense_repo = ExpenseRepository(db=db)
        self.audit = AuditRepository(db=db)
        self.accounts = AccountService(db=db)

    # ─── Чтение ────────────────────────────────────────────────────────────────

    async def list(self, fund_id: int, active_only: bool = False) -> list[TargetFundOut]:
        targets = await self.repo.list(fund_id, active_only=active_only)
        stats = await self.contribution_repo.collected_by_target_funds(fund_id)
        return [_target_fund_out(t, *stats.get(t.id, (0, 0))) for t in targets]

    async def get_detail(self, ctx: FundContext, target_fund_id: int) -> TargetFundDetailOut:
        fund_id = ctx.fund_id
        target = await self._get_or_404(fund_id, target_fund_id)
        collected, contributors = (await self.contribution_repo.collected_by_target_funds(fund_id)).get(
            target.id, (0, 0)
        )

        contributions = await self.contribution_repo.list(
            fund_id, ContributionFilters(target_fund_id=target.id), limit=100
        )
        # Отклонённые чеки в публичной истории сбора не показываем
        visible = [c for c in contributions if c.status != ContributionStatusEnum.rejected.value]
        approved = [c for c in visible if c.status == ContributionStatusEnum.approved.value]

        monthly_sums = await self.contribution_repo.approved_monthly_sums(fund_id, target_fund_id=target.id)
        today = current_period()
        monthly = [
            MonthAmountOut(period=period, amount=monthly_sums.get(period, 0))
            for period in (shift_period(today, -i) for i in reversed(range(CHART_MONTHS)))
        ]

        return TargetFundDetailOut(
            **_target_fund_out(target, collected, contributors).model_dump(),
            average_contribution=round(sum(c.credited_amount for c in approved) / len(approved)) if approved else 0,
            monthly=monthly,
            # Список взносов публичный, а сами чеки — только свои (совет видит все)
            contributions=[contribution_out(c, show_receipt=ctx.can_see_receipt(c.user_id)) for c in visible],
        )

    # ─── Совет фонда ───────────────────────────────────────────────────────────

    async def create(self, fund_id: int, user_id: int, payload: TargetFundCreateIn) -> TargetFundOut:
        await self.accounts.ensure_active_currency(fund_id, payload.currency.value)
        target = await self.repo.create(
            fund_id=fund_id,
            title=payload.title,
            description=payload.description,
            target_amount=payload.target_amount,
            currency=payload.currency.value,
            category=payload.category.value,
            created_by_id=user_id,
        )
        await self.db.commit()
        return _target_fund_out(target, 0, 0)

    async def update(self, fund_id: int, target_fund_id: int, payload: TargetFundUpdateIn) -> TargetFundOut:
        target = await self._get_or_404(fund_id, target_fund_id, for_update=True)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(target, field, value.value if hasattr(value, "value") else value)
        await self.db.commit()
        return await self._out(target)

    async def toggle(self, fund_id: int, target_fund_id: int, user_id: int) -> TargetFundOut:
        target = await self._get_or_404(fund_id, target_fund_id, for_update=True)
        target.is_active = not target.is_active
        self.audit.add(
            fund_id=fund_id,
            actor_id=user_id,
            action="target_fund.open" if target.is_active else "target_fund.close",
            entity="target_fund",
            entity_id=target.id,
            details={"title": target.title},
        )
        await self.db.commit()
        return await self._out(target)

    async def delete(self, fund_id: int, target_fund_id: int, user_id: int) -> None:
        """Удалить можно только пустой сбор (создан по ошибке). Сбор с деньгами — закрыть."""
        target = await self._get_or_404(fund_id, target_fund_id, for_update=True)
        if await self.contribution_repo.exists_for_target_fund(
            fund_id, target.id
        ) or await self.expense_repo.exists_for_target_fund(fund_id, target.id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target fund has operations, close it")

        self.audit.add(
            fund_id=fund_id,
            actor_id=user_id,
            action="target_fund.delete",
            entity="target_fund",
            entity_id=target.id,
            details={"title": target.title},
        )
        await self.repo.delete(target)
        await self.db.commit()

    # ─── Helpers ───────────────────────────────────────────────────────────────

    async def _out(self, target: TargetFund) -> TargetFundOut:
        stats = await self.contribution_repo.collected_by_target_funds(target.fund_id)
        return _target_fund_out(target, *stats.get(target.id, (0, 0)))

    async def _get_or_404(self, fund_id: int, target_fund_id: int, for_update: bool = False) -> TargetFund:
        target = await self.repo.get(fund_id, target_fund_id, for_update=for_update)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target fund not found")
        return target

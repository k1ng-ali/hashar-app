from datetime import datetime

from sqlalchemy import func, or_, select

from app.enums import PlanRequestStatusEnum
from app.models.plan_pricing import PlanDiscount, PlanPrice
from app.models.plan_request import PlanRequest
from app.repositories.base_repo import BaseRepository

# Эти заявки занимают лимит промокода; отказ лимит возвращает
USED_STATUSES = (PlanRequestStatusEnum.pending.value, PlanRequestStatusEnum.approved.value)


class PricingRepository(BaseRepository):

    # ─── Прайс ─────────────────────────────────────────────────────────────────

    async def list_prices(self) -> list[PlanPrice]:
        result = await self.db.execute(select(PlanPrice).order_by(PlanPrice.price_tjs))
        return list(result.scalars().all())

    async def get_price(self, plan: str, for_update: bool = False) -> PlanPrice | None:
        stmt = select(PlanPrice).where(PlanPrice.plan == plan)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ─── Скидки и промокоды ────────────────────────────────────────────────────

    async def list_discounts(self) -> list[PlanDiscount]:
        result = await self.db.execute(select(PlanDiscount).order_by(PlanDiscount.created_at.desc()))
        return list(result.scalars().all())

    async def list_running_sales(self, now: datetime) -> list[PlanDiscount]:
        """Включённые распродажи (без промокода), срок которых идёт прямо сейчас."""
        result = await self.db.execute(
            select(PlanDiscount).where(
                PlanDiscount.code.is_(None),
                PlanDiscount.is_active.is_(True),
                or_(PlanDiscount.starts_at.is_(None), PlanDiscount.starts_at <= now),
                or_(PlanDiscount.ends_at.is_(None), PlanDiscount.ends_at > now),
            )
        )
        return list(result.scalars().all())

    async def get_discount(self, discount_id: int, for_update: bool = False) -> PlanDiscount | None:
        stmt = select(PlanDiscount).where(PlanDiscount.id == discount_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str, for_update: bool = False) -> PlanDiscount | None:
        stmt = select(PlanDiscount).where(PlanDiscount.code == code)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_uses(self, discount_id: int, fund_id: int | None = None) -> int:
        stmt = select(func.count(PlanRequest.id)).where(
            PlanRequest.discount_id == discount_id,
            PlanRequest.status.in_(USED_STATUSES),
        )
        if fund_id is not None:
            stmt = stmt.where(PlanRequest.fund_id == fund_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def uses_by_discount(self) -> dict[int, int]:
        result = await self.db.execute(
            select(PlanRequest.discount_id, func.count(PlanRequest.id))
            .where(PlanRequest.discount_id.is_not(None), PlanRequest.status.in_(USED_STATUSES))
            .group_by(PlanRequest.discount_id)
        )
        return dict(result.all())

    async def create_discount(self, **fields) -> PlanDiscount:
        discount = PlanDiscount(**fields)
        self.db.add(discount)
        await self.db.flush()
        await self.db.refresh(discount)
        return discount

    async def delete_discount(self, discount: PlanDiscount) -> None:
        await self.db.delete(discount)

# Метод list() в классе затеняет встроенный list в аннотациях ниже (Python 3.12) — аннотации отложенные
from __future__ import annotations

from sqlalchemy import select

from app.models.target_fund import TargetFund
from app.repositories.base_repo import BaseRepository


class TargetFundRepository(BaseRepository):

    async def get(self, fund_id: int, target_fund_id: int, for_update: bool = False) -> TargetFund | None:
        stmt = select(TargetFund).where(TargetFund.id == target_fund_id, TargetFund.fund_id == fund_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, fund_id: int, active_only: bool = False) -> list[TargetFund]:
        stmt = select(TargetFund).where(TargetFund.fund_id == fund_id)
        if active_only:
            stmt = stmt.where(TargetFund.is_active == True)
        # Сначала активные, затем по дате создания
        result = await self.db.execute(stmt.order_by(TargetFund.is_active.desc(), TargetFund.created_at.desc()))
        return list(result.scalars().all())

    async def create(self, **fields) -> TargetFund:
        target_fund = TargetFund(**fields)
        self.db.add(target_fund)
        await self.db.flush()
        await self.db.refresh(target_fund)
        return target_fund

    async def delete(self, target_fund: TargetFund) -> None:
        await self.db.delete(target_fund)
        await self.db.flush()

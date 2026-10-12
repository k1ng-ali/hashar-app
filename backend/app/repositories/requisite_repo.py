# Метод list() в классе затеняет встроенный list в аннотациях ниже (Python 3.12) — аннотации отложенные
from __future__ import annotations

from sqlalchemy import select

from app.models.requisite import PaymentRequisite
from app.repositories.base_repo import BaseRepository


class RequisiteRepository(BaseRepository):

    async def get(self, fund_id: int, requisite_id: int) -> PaymentRequisite | None:
        result = await self.db.execute(
            select(PaymentRequisite).where(PaymentRequisite.id == requisite_id, PaymentRequisite.fund_id == fund_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        fund_id: int,
        active_only: bool = False,
        currencies: list[str] | None = None,
    ) -> list[PaymentRequisite]:
        stmt = select(PaymentRequisite).where(PaymentRequisite.fund_id == fund_id)
        if active_only:
            stmt = stmt.where(PaymentRequisite.is_active == True)
        if currencies is not None:
            stmt = stmt.where(PaymentRequisite.currency.in_(currencies))
        result = await self.db.execute(stmt.order_by(PaymentRequisite.currency, PaymentRequisite.id))
        return list(result.scalars().all())

    async def create(self, **fields) -> PaymentRequisite:
        requisite = PaymentRequisite(**fields)
        self.db.add(requisite)
        await self.db.flush()
        await self.db.refresh(requisite)
        return requisite

    async def delete(self, requisite: PaymentRequisite) -> None:
        await self.db.delete(requisite)
        await self.db.flush()

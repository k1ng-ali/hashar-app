# Метод list() в классе затеняет встроенный list в аннотациях ниже (Python 3.12) — аннотации отложенные
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.transfer import AccountTransfer
from app.repositories.base_repo import BaseRepository


class TransferRepository(BaseRepository):

    async def get(self, fund_id: int, transfer_id: int) -> AccountTransfer | None:
        result = await self.db.execute(
            select(AccountTransfer)
            .where(AccountTransfer.id == transfer_id, AccountTransfer.fund_id == fund_id)
            .options(selectinload(AccountTransfer.created_by))
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def list(self, fund_id: int, skip: int = 0, limit: int = 50) -> list[AccountTransfer]:
        result = await self.db.execute(
            select(AccountTransfer)
            .where(AccountTransfer.fund_id == fund_id)
            .options(selectinload(AccountTransfer.created_by))
            .order_by(AccountTransfer.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def sums_by_currency(
        self,
        fund_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> tuple[dict[str, int], dict[str, int]]:
        """(зачислено по валютам, списано по валютам)."""
        incoming: dict[str, int] = {}
        outgoing: dict[str, int] = {}
        for side, currency_col, amount_col in (
            (incoming, AccountTransfer.to_currency, AccountTransfer.to_amount),
            (outgoing, AccountTransfer.from_currency, AccountTransfer.from_amount),
        ):
            stmt = select(currency_col, func.sum(amount_col)).where(
                AccountTransfer.fund_id == fund_id, currency_col.is_not(None)
            )
            if start:
                stmt = stmt.where(AccountTransfer.created_at >= start)
            if end:
                stmt = stmt.where(AccountTransfer.created_at < end)
            result = await self.db.execute(stmt.group_by(currency_col))
            side.update({currency: int(total or 0) for currency, total in result.all()})
        return incoming, outgoing

    async def create(self, **fields) -> AccountTransfer:
        transfer = AccountTransfer(**fields)
        self.db.add(transfer)
        await self.db.flush()
        return await self.get(transfer.fund_id, transfer.id)

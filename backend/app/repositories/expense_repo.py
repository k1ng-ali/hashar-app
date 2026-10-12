from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.expense import Expense
from app.repositories.base_repo import BaseRepository


def _with_relations(stmt):
    return stmt.options(selectinload(Expense.created_by), selectinload(Expense.target_fund))


class ExpenseRepository(BaseRepository):

    async def get(self, fund_id: int, expense_id: int) -> Expense | None:
        stmt = _with_relations(select(Expense).where(Expense.id == expense_id, Expense.fund_id == fund_id))
        result = await self.db.execute(stmt.execution_options(populate_existing=True))
        return result.scalar_one_or_none()

    async def list(
        self,
        fund_id: int,
        category: str | None = None,
        currency: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Expense]:
        stmt = select(Expense).where(Expense.fund_id == fund_id)
        if category:
            stmt = stmt.where(Expense.category == category)
        if currency:
            stmt = stmt.where(Expense.currency == currency)
        stmt = _with_relations(stmt.order_by(Expense.created_at.desc()).offset(skip).limit(limit))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def sums_by_currency(
        self,
        fund_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict[str, int]:
        stmt = select(Expense.currency, func.sum(Expense.amount)).where(Expense.fund_id == fund_id)
        if start:
            stmt = stmt.where(Expense.created_at >= start)
        if end:
            stmt = stmt.where(Expense.created_at < end)
        result = await self.db.execute(stmt.group_by(Expense.currency))
        return {currency: int(total or 0) for currency, total in result.all()}

    async def sums_by_category(self, fund_id: int, currency: str) -> dict[str, int]:
        result = await self.db.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(Expense.fund_id == fund_id, Expense.currency == currency)
            .group_by(Expense.category)
        )
        return {category: int(total or 0) for category, total in result.all()}

    async def monthly_sums(self, fund_id: int, currency: str) -> dict[str, int]:
        period = func.to_char(Expense.created_at, "YYYY-MM")
        result = await self.db.execute(
            select(period, func.sum(Expense.amount))
            .where(Expense.fund_id == fund_id, Expense.currency == currency)
            .group_by(period)
        )
        return {p: int(total or 0) for p, total in result.all()}

    async def create(self, **fields) -> Expense:
        expense = Expense(**fields)
        self.db.add(expense)
        await self.db.flush()
        return await self.get(expense.fund_id, expense.id)

    async def delete(self, expense: Expense) -> None:
        await self.db.delete(expense)
        await self.db.flush()

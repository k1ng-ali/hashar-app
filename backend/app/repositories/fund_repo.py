from sqlalchemy import func, or_, select

from app.models.fund import Fund, FundAccount
from app.repositories.base_repo import BaseRepository


class FundRepository(BaseRepository):

    # ─── Фонды ─────────────────────────────────────────────────────────────────

    async def get(self, fund_id: int, for_update: bool = False) -> Fund | None:
        stmt = select(Fund).where(Fund.id == fund_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Fund | None:
        result = await self.db.execute(select(Fund).where(Fund.code == code.upper()))
        return result.scalar_one_or_none()

    async def code_exists(self, code: str) -> bool:
        result = await self.db.execute(select(Fund.id).where(Fund.code == code))
        return result.scalar_one_or_none() is not None

    async def search(self, query: str, limit: int = 20) -> list[Fund]:
        """Точное совпадение по коду или подстрока в названии."""
        stmt = (
            select(Fund)
            .where(or_(Fund.code == query.upper(), Fund.name.ilike(f"%{query}%")))
            .order_by(Fund.name)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, skip: int = 0, limit: int = 50) -> list[Fund]:
        result = await self.db.execute(select(Fund).order_by(Fund.created_at.desc()).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(Fund.id)))
        return result.scalar() or 0

    async def create(self, **fields) -> Fund:
        fund = Fund(**fields)
        self.db.add(fund)
        await self.db.flush()
        await self.db.refresh(fund)
        return fund

    # ─── Счета ─────────────────────────────────────────────────────────────────

    async def list_accounts(self, fund_id: int, active_only: bool = False) -> list[FundAccount]:
        stmt = select(FundAccount).where(FundAccount.fund_id == fund_id)
        if active_only:
            stmt = stmt.where(FundAccount.is_active == True)
        result = await self.db.execute(stmt.order_by(FundAccount.id))
        return list(result.scalars().all())

    async def get_account(self, fund_id: int, currency: str) -> FundAccount | None:
        result = await self.db.execute(
            select(FundAccount).where(FundAccount.fund_id == fund_id, FundAccount.currency == currency)
        )
        return result.scalar_one_or_none()

    async def create_account(self, fund_id: int, currency: str) -> FundAccount:
        account = FundAccount(fund_id=fund_id, currency=currency)
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account

from sqlalchemy import select

from app.core.finance import RateSchedule
from app.models.fund_rate import FundRate
from app.repositories.base_repo import BaseRepository


class FundRateRepository(BaseRepository):

    async def list(self, fund_id: int) -> list[FundRate]:
        result = await self.db.execute(select(FundRate).where(FundRate.fund_id == fund_id).order_by(FundRate.period))
        return list(result.scalars().all())

    async def schedule(self, fund_id: int) -> RateSchedule:
        """[(период, тариф)] по возрастанию — для расчёта сальдо."""
        return [(rate.period, rate.amount) for rate in await self.list(fund_id)]

    async def get(self, fund_id: int, period: str) -> FundRate | None:
        result = await self.db.execute(select(FundRate).where(FundRate.fund_id == fund_id, FundRate.period == period))
        return result.scalar_one_or_none()

    async def create(self, **fields) -> FundRate:
        rate = FundRate(**fields)
        self.db.add(rate)
        await self.db.flush()
        return rate

    async def delete(self, rate: FundRate) -> None:
        await self.db.delete(rate)
        await self.db.flush()

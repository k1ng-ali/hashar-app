from sqlalchemy import select

from app.core.finance import periods_range
from app.models.accrual_pause import MemberAccrualPause
from app.repositories.base_repo import BaseRepository


class AccrualPauseRepository(BaseRepository):

    async def excluded_periods(self, fund_id: int, member_ids: list[int]) -> dict[int, set[str]]:
        """{member_id: {"YYYY-MM", ...}} — месяцы, за которые совет решил не начислять взнос."""
        if not member_ids:
            return {}
        result = await self.db.execute(
            select(MemberAccrualPause).where(
                MemberAccrualPause.fund_id == fund_id, MemberAccrualPause.member_id.in_(member_ids)
            )
        )
        excluded: dict[int, set[str]] = {}
        for pause in result.scalars().all():
            excluded.setdefault(pause.member_id, set()).update(periods_range(pause.from_period, pause.to_period))
        return excluded

    async def create(self, **fields) -> MemberAccrualPause:
        pause = MemberAccrualPause(**fields)
        self.db.add(pause)
        await self.db.flush()
        return pause

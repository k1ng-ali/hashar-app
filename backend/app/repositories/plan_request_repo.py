# Метод list() в классе затеняет встроенный list в аннотациях ниже (Python 3.12) — аннотации отложенные
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.enums import PlanRequestStatusEnum
from app.models.plan_request import PlanRequest
from app.repositories.base_repo import BaseRepository


def _with_relations(stmt):
    return stmt.options(selectinload(PlanRequest.fund), selectinload(PlanRequest.requested_by))


class PlanRequestRepository(BaseRepository):

    async def get(self, request_id: int, for_update: bool = False) -> PlanRequest | None:
        stmt = _with_relations(select(PlanRequest).where(PlanRequest.id == request_id))
        stmt = stmt.execution_options(populate_existing=True)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        status: str | None = None,
        fund_id: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[PlanRequest]:
        stmt = select(PlanRequest)
        if status:
            stmt = stmt.where(PlanRequest.status == status)
        if fund_id is not None:
            stmt = stmt.where(PlanRequest.fund_id == fund_id)
        stmt = _with_relations(stmt.order_by(PlanRequest.created_at.desc()).offset(skip).limit(limit))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def has_pending(self, fund_id: int) -> bool:
        result = await self.db.execute(
            select(PlanRequest.id).where(
                PlanRequest.fund_id == fund_id,
                PlanRequest.status == PlanRequestStatusEnum.pending.value,
            )
        )
        return result.first() is not None

    async def create(self, **fields) -> PlanRequest:
        request = PlanRequest(**fields)
        self.db.add(request)
        await self.db.flush()
        return await self.get(request.id)

# Метод list() в классе затеняет встроенный list в аннотациях ниже (Python 3.12) — аннотации отложенные
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_repo import AuditRepository
from app.schemas.audit import AuditEventOut


class AuditService:
    """Журнал действий фонда — только чтение. Записывают его сами сервисы через AuditRepository.add."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuditRepository(db=db)

    async def list(self, fund_id: int, skip: int = 0, limit: int = 50) -> list[AuditEventOut]:
        return [
            AuditEventOut(
                id=event.id,
                action=event.action,
                entity=event.entity,
                entity_id=event.entity_id,
                details=event.details or {},
                actor_id=event.actor_id,
                actor_name=event.actor.full_name if event.actor else None,
                created_at=event.created_at,
            )
            for event in await self.repo.list(fund_id, skip=skip, limit=limit)
        ]

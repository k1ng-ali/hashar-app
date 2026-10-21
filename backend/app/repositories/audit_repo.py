# Метод list() в классе затеняет встроенный list в аннотациях ниже (Python 3.12) — аннотации отложенные
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.audit_event import AuditEvent
from app.repositories.base_repo import BaseRepository


class AuditRepository(BaseRepository):

    def add(
        self,
        fund_id: int | None,
        actor_id: int | None,
        action: str,
        entity: str,
        entity_id: int | None = None,
        details: dict | None = None,
    ) -> None:
        """Запись уходит в БД вместе с commit сервиса — в одной транзакции с самим действием."""
        self.db.add(
            AuditEvent(
                fund_id=fund_id,
                actor_id=actor_id,
                action=action,
                entity=entity,
                entity_id=entity_id,
                details=details or {},
            )
        )

    async def list(self, fund_id: int, skip: int = 0, limit: int = 50) -> list[AuditEvent]:
        result = await self.db.execute(
            select(AuditEvent)
            .where(AuditEvent.fund_id == fund_id)
            .options(selectinload(AuditEvent.actor))
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_for_entity(self, fund_id: int, entity: str, entity_id: int, limit: int = 50) -> list[AuditEvent]:
        """История одной записи (например, правки сбора) — новые первыми."""
        result = await self.db.execute(
            select(AuditEvent)
            .where(AuditEvent.fund_id == fund_id, AuditEvent.entity == entity, AuditEvent.entity_id == entity_id)
            .options(selectinload(AuditEvent.actor))
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

# Метод list() в классе затеняет встроенный list в аннотациях ниже — аннотации отложенные
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.models.fund import Fund
from app.models.fund_notice import FundNotice
from app.models.user import User
from app.repositories.base_repo import BaseRepository


class NoticeRepository(BaseRepository):

    def add(
        self,
        fund_id: int,
        kind: str,
        text: str | None = None,
        details: dict | None = None,
        author_id: int | None = None,
    ) -> FundNotice:
        """Уходит в БД вместе с commit сервиса — в одной транзакции с действием (например, отказом)."""
        notice = FundNotice(fund_id=fund_id, kind=kind, text=text, details=details or {}, author_id=author_id)
        self.db.add(notice)
        return notice

    async def add_once(self, dedupe_key: str, fund_id: int, kind: str, details: dict) -> bool:
        """Автоматическое уведомление: второй раз с тем же ключом не создаётся. True — создано сейчас."""
        result = await self.db.execute(
            insert(FundNotice)
            .values(fund_id=fund_id, kind=kind, details=details, dedupe_key=dedupe_key)
            .on_conflict_do_nothing(index_elements=["dedupe_key"])
            .returning(FundNotice.id)
        )
        return result.scalar_one_or_none() is not None

    async def list(self, fund_id: int, skip: int = 0, limit: int = 50) -> list[FundNotice]:
        result = await self.db.execute(
            select(FundNotice)
            .where(FundNotice.fund_id == fund_id)
            .order_by(FundNotice.created_at.desc(), FundNotice.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_since(self, fund_id: int, since: datetime | None) -> int:
        stmt = select(func.count(FundNotice.id)).where(FundNotice.fund_id == fund_id)
        if since is not None:
            stmt = stmt.where(FundNotice.created_at > since)
        return int((await self.db.execute(stmt)).scalar() or 0)

    async def list_all(self, fund_id: int | None = None, skip: int = 0, limit: int = 50) -> list:
        """Для админа платформы: уведомления всех фондов с названием фонда и автором."""
        stmt = (
            select(FundNotice, Fund.name.label("fund_name"), User.full_name.label("author_name"))
            .join(Fund, Fund.id == FundNotice.fund_id)
            .outerjoin(User, User.id == FundNotice.author_id)
        )
        if fund_id is not None:
            stmt = stmt.where(FundNotice.fund_id == fund_id)
        result = await self.db.execute(
            stmt.order_by(FundNotice.created_at.desc(), FundNotice.id.desc()).offset(skip).limit(limit)
        )
        return list(result.all())

    async def list_funds_by_expiry(self, start: datetime, end: datetime) -> list[Fund]:
        """Платные фонды, у которых тариф заканчивается в окне [start, end)."""
        result = await self.db.execute(
            select(Fund).where(Fund.plan != "free", Fund.plan_expires_at >= start, Fund.plan_expires_at < end)
        )
        return list(result.scalars().all())

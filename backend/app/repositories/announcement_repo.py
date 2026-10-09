from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.models.announcement import Announcement, AnnouncementComment, AnnouncementLike
from app.models.transfer import AccountTransfer
from app.repositories.base_repo import BaseRepository


def _with_relations(stmt):
    return stmt.options(
        selectinload(Announcement.author),
        selectinload(Announcement.transfer).selectinload(AccountTransfer.created_by),
        selectinload(Announcement.comments).selectinload(AnnouncementComment.user),
    )


class AnnouncementRepository(BaseRepository):

    # ─── Объявления ────────────────────────────────────────────────────────────

    async def get(self, fund_id: int, announcement_id: int) -> Announcement | None:
        stmt = _with_relations(
            select(Announcement).where(Announcement.id == announcement_id, Announcement.fund_id == fund_id)
        )
        result = await self.db.execute(stmt.execution_options(populate_existing=True))
        return result.scalar_one_or_none()

    async def list(
        self,
        fund_id: int,
        category: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Announcement]:
        stmt = select(Announcement).where(Announcement.fund_id == fund_id)
        if category:
            stmt = stmt.where(Announcement.category == category)
        # Закреплённые всегда сверху
        stmt = stmt.order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(_with_relations(stmt))
        return list(result.scalars().all())

    async def create(self, **fields) -> Announcement:
        announcement = Announcement(**fields)
        self.db.add(announcement)
        await self.db.flush()
        return await self.get(announcement.fund_id, announcement.id)

    async def delete(self, announcement: Announcement) -> None:
        await self.db.delete(announcement)
        await self.db.flush()

    # ─── Комментарии ───────────────────────────────────────────────────────────

    async def create_comment(
        self,
        announcement_id: int,
        user_id: int,
        user_unit: str | None,
        text: str,
    ) -> AnnouncementComment:
        comment = AnnouncementComment(announcement_id=announcement_id, user_id=user_id, user_unit=user_unit, text=text)
        self.db.add(comment)
        await self.db.flush()
        result = await self.db.execute(
            select(AnnouncementComment)
            .where(AnnouncementComment.id == comment.id)
            .options(selectinload(AnnouncementComment.user))
            .execution_options(populate_existing=True)
        )
        return result.scalar_one()

    # ─── Лайки ─────────────────────────────────────────────────────────────────

    async def likes_count(self, announcement_ids: list[int]) -> dict[int, int]:
        if not announcement_ids:
            return {}
        result = await self.db.execute(
            select(AnnouncementLike.announcement_id, func.count(AnnouncementLike.id))
            .where(AnnouncementLike.announcement_id.in_(announcement_ids))
            .group_by(AnnouncementLike.announcement_id)
        )
        return {announcement_id: int(count) for announcement_id, count in result.all()}

    async def liked_ids(self, user_id: int, announcement_ids: list[int]) -> set[int]:
        if not announcement_ids:
            return set()
        result = await self.db.execute(
            select(AnnouncementLike.announcement_id).where(
                AnnouncementLike.user_id == user_id,
                AnnouncementLike.announcement_id.in_(announcement_ids),
            )
        )
        return set(result.scalars().all())

    async def add_like(self, announcement_id: int, user_id: int) -> None:
        self.db.add(AnnouncementLike(announcement_id=announcement_id, user_id=user_id))
        await self.db.flush()

    async def remove_like(self, announcement_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            delete(AnnouncementLike).where(
                AnnouncementLike.announcement_id == announcement_id,
                AnnouncementLike.user_id == user_id,
            )
        )
        return result.rowcount > 0

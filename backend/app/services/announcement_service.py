from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import AnnouncementCategoryEnum
from app.models.announcement import Announcement, AnnouncementComment
from app.repositories.announcement_repo import AnnouncementRepository
from app.repositories.member_repo import MemberRepository
from app.schemas.announcement import AnnouncementCreateIn, AnnouncementOut, CommentOut
from app.schemas.member import FundContext
from app.services.account_service import transfer_out


def _comment_out(comment: AnnouncementComment) -> CommentOut:
    return CommentOut(
        id=comment.id,
        user_id=comment.user_id,
        user_name=comment.user.full_name,
        user_unit=comment.user_unit,
        text=comment.text,
        created_at=comment.created_at,
    )


class AnnouncementService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AnnouncementRepository(db=db)
        self.member_repo = MemberRepository(db=db)

    async def list(
        self,
        ctx: FundContext,
        category: AnnouncementCategoryEnum | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AnnouncementOut]:
        items = await self.repo.list(
            ctx.fund_id,
            category=category.value if category else None,
            skip=skip,
            limit=limit,
        )
        return await self._out_many(ctx.fund_id, items, user_id=ctx.user_id)

    async def create(self, ctx: FundContext, payload: AnnouncementCreateIn) -> AnnouncementOut:
        # Закреплять объявления может только совет — участнику молча снимаем флаг
        announcement = await self.repo.create(
            fund_id=ctx.fund_id,
            title=payload.title,
            content=payload.content,
            category=payload.category.value,
            is_pinned=payload.is_pinned and ctx.is_council,
            author_id=ctx.user_id,
        )
        await self.db.commit()
        return (await self._out_many(ctx.fund_id, [announcement], user_id=ctx.user_id))[0]

    async def toggle_like(self, ctx: FundContext, announcement_id: int) -> AnnouncementOut:
        await self._get_or_404(ctx.fund_id, announcement_id)

        removed = await self.repo.remove_like(announcement_id=announcement_id, user_id=ctx.user_id)
        if not removed:
            try:
                await self.repo.add_like(announcement_id=announcement_id, user_id=ctx.user_id)
            except IntegrityError:
                # Параллельный двойной клик — лайк уже стоит
                await self.db.rollback()
        await self.db.commit()

        announcement = await self._get_or_404(ctx.fund_id, announcement_id)
        return (await self._out_many(ctx.fund_id, [announcement], user_id=ctx.user_id))[0]

    async def add_comment(self, ctx: FundContext, announcement_id: int, text: str) -> CommentOut:
        await self._get_or_404(ctx.fund_id, announcement_id)
        member = await self.member_repo.get_by_user(ctx.fund_id, ctx.user_id)
        comment = await self.repo.create_comment(
            announcement_id=announcement_id,
            user_id=ctx.user_id,
            user_unit=member.address_unit if member else None,
            text=text.strip(),
        )
        await self.db.commit()
        return _comment_out(comment)

    async def delete(self, ctx: FundContext, announcement_id: int) -> None:
        announcement = await self._get_or_404(ctx.fund_id, announcement_id)
        # Объявление о движении по счетам удалить нельзя — это след для прозрачности
        if announcement.transfer_id is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Finance announcements cannot be deleted")
        # Удалить может автор или председатель
        if announcement.author_id != ctx.user_id and not ctx.is_chairman:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")
        await self.repo.delete(announcement)
        await self.db.commit()

    # ─── Helpers ───────────────────────────────────────────────────────────────

    async def _out_many(self, fund_id: int, items: list[Announcement], user_id: int) -> list[AnnouncementOut]:
        ids = [item.id for item in items]
        likes = await self.repo.likes_count(ids)
        liked = await self.repo.liked_ids(user_id=user_id, announcement_ids=ids)
        authors = await self.member_repo.units_by_users(fund_id, list({item.author_id for item in items}))

        return [
            AnnouncementOut(
                id=item.id,
                title=item.title,
                content=item.content,
                category=item.category,
                is_pinned=item.is_pinned,
                author_id=item.author_id,
                author_name=item.author.full_name,
                author_role=authors[item.author_id][1] if item.author_id in authors else None,
                likes_count=likes.get(item.id, 0),
                is_liked=item.id in liked,
                comments=[_comment_out(c) for c in item.comments],
                transfer=transfer_out(item.transfer) if item.transfer else None,
                created_at=item.created_at,
            )
            for item in items
        ]

    async def _get_or_404(self, fund_id: int, announcement_id: int) -> Announcement:
        announcement = await self.repo.get(fund_id, announcement_id)
        if not announcement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
        return announcement

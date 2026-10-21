# Метод list() затеняет встроенный list в аннотациях ниже — аннотации отложенные
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import PLAN_EXPIRY_WARNING, PLAN_GRACE, blocks_at, free_limit
from app.models.fund_notice import FundNotice
from app.repositories.audit_repo import AuditRepository
from app.repositories.fund_repo import FundRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.notice_repo import NoticeRepository
from app.schemas.member import FundContext
from app.schemas.notice import NoticeListOut, NoticeOut, NoticeOutAdmin

logger = logging.getLogger(__name__)

# Если фоновая задача какое-то время не работала, о блокировке взносов всё равно сообщим —
# но не о том, что случилось давно
LAPSED_CATCH_UP = timedelta(days=3)


def notice_out(notice: FundNotice, read_at: datetime | None = None) -> NoticeOut:
    return NoticeOut(
        id=notice.id,
        kind=notice.kind,
        text=notice.text,
        details=notice.details or {},
        is_unread=read_at is None or notice.created_at > read_at,
        created_at=notice.created_at,
    )


def plan_details(fund) -> dict:
    """Снимок тарифа для текста уведомления."""
    block = blocks_at(fund)
    return {
        "plan": fund.plan,
        "expires_at": fund.plan_expires_at.isoformat() if fund.plan_expires_at else None,
        "blocks_at": block.isoformat() if block else None,
    }


class NoticeService:
    """Уведомления совету фонда от платформы: сообщения админа, решения по тарифу, окончание тарифа."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NoticeRepository(db=db)
        self.fund_repo = FundRepository(db=db)
        self.member_repo = MemberRepository(db=db)
        self.audit = AuditRepository(db=db)

    # ─── Совет фонда ───────────────────────────────────────────────────────────

    async def list(self, ctx: FundContext, skip: int = 0, limit: int = 50) -> NoticeListOut:
        member = await self.member_repo.get_by_user(ctx.fund_id, ctx.user_id)
        read_at = member.notices_read_at if member else None
        return NoticeListOut(
            items=[notice_out(n, read_at) for n in await self.repo.list(ctx.fund_id, skip=skip, limit=limit)],
            unread=await self.repo.count_since(ctx.fund_id, read_at),
        )

    async def mark_read(self, ctx: FundContext) -> None:
        member = await self.member_repo.get_by_user(ctx.fund_id, ctx.user_id)
        if member:
            member.notices_read_at = datetime.now(timezone.utc)
            await self.db.commit()

    # ─── Админ платформы ───────────────────────────────────────────────────────

    async def send(self, fund_id: int, admin_id: int, text: str) -> NoticeOutAdmin:
        fund = await self.fund_repo.get(fund_id)
        if not fund:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fund not found")

        notice = self.repo.add(fund_id=fund.id, kind="admin_message", text=text.strip(), author_id=admin_id)
        await self.db.flush()
        self.audit.add(
            fund_id=fund.id,
            actor_id=admin_id,
            action="notice.send",
            entity="fund",
            entity_id=fund.id,
            details={"notice_id": notice.id, "text": notice.text},
        )
        await self.db.commit()
        await self.db.refresh(notice)
        return NoticeOutAdmin(**notice_out(notice).model_dump(), fund_id=fund.id, fund_name=fund.name)

    async def list_admin(self, fund_id: int | None = None, skip: int = 0, limit: int = 50) -> list[NoticeOutAdmin]:
        return [
            NoticeOutAdmin(
                **notice_out(row.FundNotice).model_dump(),
                fund_id=row.FundNotice.fund_id,
                fund_name=row.fund_name,
                author_name=row.author_name,
            )
            for row in await self.repo.list_all(fund_id=fund_id, skip=skip, limit=limit)
        ]

    # ─── Фоновая проверка окончания тарифов ────────────────────────────────────

    async def check_plan_expiry(self, now: datetime | None = None) -> int:
        """
        Автоматические уведомления совету:
        за 3 дня до окончания тарифа, в момент окончания (идёт льготный срок)
        и когда льготный срок прошёл, а взносы жителей заблокированы.
        Повторно не создаются (dedupe_key по фонду и дате окончания). Возвращает число новых.
        """
        now = now or datetime.now(timezone.utc)
        created = 0

        for fund in await self.repo.list_funds_by_expiry(now, now + PLAN_EXPIRY_WARNING):
            created += await self._once("plan_expiring", fund, plan_details(fund))

        for fund in await self.repo.list_funds_by_expiry(now - PLAN_GRACE, now):
            will_block = await self.member_repo.count_active(fund.id) > free_limit()
            created += await self._once("plan_expired", fund, {**plan_details(fund), "will_block": will_block})

        for fund in await self.repo.list_funds_by_expiry(now - PLAN_GRACE - LAPSED_CATCH_UP, now - PLAN_GRACE):
            # Фонд помещается в Free — блокировать нечего, а об окончании тарифа уже сообщили
            if await self.member_repo.count_active(fund.id) > free_limit():
                created += await self._once("plan_lapsed", fund, plan_details(fund))

        await self.db.commit()
        if created:
            logger.info("Plan expiry notices created: %s", created)
        return created

    async def _once(self, kind: str, fund, details: dict) -> int:
        key = f"{kind}:{fund.id}:{fund.plan_expires_at.isoformat()}"
        return int(await self.repo.add_once(key, fund_id=fund.id, kind=kind, details=details))

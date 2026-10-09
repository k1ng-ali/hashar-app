"""
Доступ к фонду из URL (/funds/{fund_id}/...).

Роль в фонде не хранится в JWT: на каждый запрос проверяем активное членство в БД,
чтобы блокировка или снятие роли действовали сразу.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps.auth import get_current_user
from app.enums import FundRoleEnum, MemberStatusEnum
from app.repositories.member_repo import MemberRepository
from app.schemas.member import FundContext
from app.schemas.user import CurrentUser


async def get_fund_context(
    fund_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FundContext:
    member = await MemberRepository(db=db).get_by_user(fund_id=fund_id, user_id=user.id)
    if not member or member.status != MemberStatusEnum.active.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this fund")
    return FundContext(fund_id=fund_id, user_id=user.id, member_id=member.id, role=member.role)


async def require_fund_council(ctx: FundContext = Depends(get_fund_context)) -> FundContext:
    """Совет фонда: ревизоры и председатель."""
    if not ctx.is_council:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")
    return ctx


async def require_fund_chairman(ctx: FundContext = Depends(get_fund_context)) -> FundContext:
    if ctx.role != FundRoleEnum.chairman:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the chairman can do this")
    return ctx

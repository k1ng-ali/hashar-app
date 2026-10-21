from fastapi import APIRouter, Depends, Query, status

from app.deps.fund import require_fund_council
from app.deps.services import get_notice_service
from app.schemas.member import FundContext
from app.schemas.notice import NoticeListOut
from app.services.notice_service import NoticeService

# Уведомления от платформы видит совет фонда: председатель и администраторы
router = APIRouter(prefix="/funds/{fund_id}/notices", tags=["Council • Notices"])


@router.get("/", response_model=NoticeListOut)
async def list_notices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    ctx: FundContext = Depends(require_fund_council),
    service: NoticeService = Depends(get_notice_service),
):
    return await service.list(ctx, skip=skip, limit=limit)


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notices_read(
    ctx: FundContext = Depends(require_fund_council),
    service: NoticeService = Depends(get_notice_service),
):
    await service.mark_read(ctx)

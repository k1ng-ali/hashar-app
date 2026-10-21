from fastapi import APIRouter, Depends, Query, status

from app.deps.auth import require_platform_admin
from app.deps.services import get_notice_service
from app.schemas.notice import NoticeIn, NoticeOutAdmin
from app.schemas.user import CurrentUser
from app.services.notice_service import NoticeService

router = APIRouter(tags=["Admin • Notices"])


@router.get("/notices", response_model=list[NoticeOutAdmin])
async def list_notices(
    fund_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: CurrentUser = Depends(require_platform_admin),
    service: NoticeService = Depends(get_notice_service),
):
    return await service.list_admin(fund_id=fund_id, skip=skip, limit=limit)


@router.post("/funds/{fund_id}/notices", response_model=NoticeOutAdmin, status_code=status.HTTP_201_CREATED)
async def send_notice(
    fund_id: int,
    payload: NoticeIn,
    user: CurrentUser = Depends(require_platform_admin),
    service: NoticeService = Depends(get_notice_service),
):
    return await service.send(fund_id=fund_id, admin_id=user.id, text=payload.text)

from fastapi import APIRouter, Depends

from app.deps.fund import require_fund_council
from app.deps.services import get_announcement_service
from app.schemas.announcement import AnnouncementOut, AnnouncementPinIn
from app.schemas.member import FundContext
from app.services.announcement_service import AnnouncementService

router = APIRouter(prefix="/funds/{fund_id}/announcements", tags=["Council • Announcements"])


@router.put("/{announcement_id}/pin", response_model=AnnouncementOut)
async def set_pinned(
    announcement_id: int,
    payload: AnnouncementPinIn,
    ctx: FundContext = Depends(require_fund_council),
    service: AnnouncementService = Depends(get_announcement_service),
):
    return await service.set_pinned(ctx=ctx, announcement_id=announcement_id, is_pinned=payload.is_pinned)

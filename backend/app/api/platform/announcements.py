from fastapi import APIRouter, Depends, Query, status

from app.deps.fund import get_fund_context
from app.deps.services import get_announcement_service
from app.enums import AnnouncementCategoryEnum
from app.schemas.announcement import AnnouncementCreateIn, AnnouncementOut, CommentCreateIn, CommentOut
from app.schemas.member import FundContext
from app.services.announcement_service import AnnouncementService

router = APIRouter(prefix="/funds/{fund_id}/announcements", tags=["Platform • Announcements"])


@router.get("/", response_model=list[AnnouncementOut])
async def list_announcements(
    category: AnnouncementCategoryEnum | None = None,
    skip: int = 0,
    limit: int = Query(50, ge=1, le=100),
    ctx: FundContext = Depends(get_fund_context),
    service: AnnouncementService = Depends(get_announcement_service),
):
    return await service.list(ctx=ctx, category=category, skip=skip, limit=limit)


@router.post("/", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    payload: AnnouncementCreateIn,
    ctx: FundContext = Depends(get_fund_context),
    service: AnnouncementService = Depends(get_announcement_service),
):
    return await service.create(ctx=ctx, payload=payload)


@router.post("/{announcement_id}/like", response_model=AnnouncementOut)
async def toggle_like(
    announcement_id: int,
    ctx: FundContext = Depends(get_fund_context),
    service: AnnouncementService = Depends(get_announcement_service),
):
    return await service.toggle_like(ctx=ctx, announcement_id=announcement_id)


@router.post("/{announcement_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(
    announcement_id: int,
    payload: CommentCreateIn,
    ctx: FundContext = Depends(get_fund_context),
    service: AnnouncementService = Depends(get_announcement_service),
):
    return await service.add_comment(ctx=ctx, announcement_id=announcement_id, text=payload.text)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: int,
    ctx: FundContext = Depends(get_fund_context),
    service: AnnouncementService = Depends(get_announcement_service),
):
    await service.delete(ctx=ctx, announcement_id=announcement_id)

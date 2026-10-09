from fastapi import APIRouter, Depends, Query

from app.deps.fund import require_fund_council
from app.deps.services import get_contribution_service
from app.enums import ContributionCategoryEnum, ContributionStatusEnum
from app.schemas.contribution import ContributionApproveIn, ContributionOut, ContributionRejectIn
from app.schemas.member import FundContext
from app.services.contribution_service import ContributionService

router = APIRouter(prefix="/funds/{fund_id}/contributions", tags=["Council • Contributions"])


@router.get("/", response_model=list[ContributionOut])
async def list_contributions(
    status_filter: ContributionStatusEnum | None = Query(None, alias="status"),
    category: ContributionCategoryEnum | None = None,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = Query(50, ge=1, le=100),
    ctx: FundContext = Depends(require_fund_council),
    service: ContributionService = Depends(get_contribution_service),
):
    return await service.list_all(
        fund_id=ctx.fund_id,
        status_filter=status_filter,
        category=category,
        user_id=user_id,
        skip=skip,
        limit=limit,
    )


@router.post("/{contribution_id}/approve", response_model=ContributionOut)
async def approve_contribution(
    contribution_id: int,
    payload: ContributionApproveIn,
    ctx: FundContext = Depends(require_fund_council),
    service: ContributionService = Depends(get_contribution_service),
):
    return await service.approve(
        fund_id=ctx.fund_id,
        contribution_id=contribution_id,
        reviewer_id=ctx.user_id,
        comment=payload.comment_admin,
    )


@router.post("/{contribution_id}/reject", response_model=ContributionOut)
async def reject_contribution(
    contribution_id: int,
    payload: ContributionRejectIn,
    ctx: FundContext = Depends(require_fund_council),
    service: ContributionService = Depends(get_contribution_service),
):
    return await service.reject(
        fund_id=ctx.fund_id,
        contribution_id=contribution_id,
        reviewer_id=ctx.user_id,
        reason=payload.comment_admin,
    )

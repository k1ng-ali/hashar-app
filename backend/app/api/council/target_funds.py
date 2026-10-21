from fastapi import APIRouter, Depends, status

from app.deps.fund import require_fund_chairman, require_fund_council
from app.deps.services import get_target_fund_service
from app.schemas.member import FundContext
from app.schemas.target_fund import TargetFundCreateIn, TargetFundOut, TargetFundUpdateIn
from app.services.target_fund_service import TargetFundService

router = APIRouter(prefix="/funds/{fund_id}/target-funds", tags=["Council • Target funds"])


@router.post("/", response_model=TargetFundOut, status_code=status.HTTP_201_CREATED)
async def create_target_fund(
    payload: TargetFundCreateIn,
    ctx: FundContext = Depends(require_fund_council),
    service: TargetFundService = Depends(get_target_fund_service),
):
    return await service.create(fund_id=ctx.fund_id, user_id=ctx.user_id, payload=payload)


@router.patch("/{target_fund_id}", response_model=TargetFundOut)
async def update_target_fund(
    target_fund_id: int,
    payload: TargetFundUpdateIn,
    ctx: FundContext = Depends(require_fund_council),
    service: TargetFundService = Depends(get_target_fund_service),
):
    return await service.update(
        fund_id=ctx.fund_id, target_fund_id=target_fund_id, user_id=ctx.user_id, payload=payload
    )


@router.post("/{target_fund_id}/toggle", response_model=TargetFundOut)
async def toggle_target_fund(
    target_fund_id: int,
    ctx: FundContext = Depends(require_fund_council),
    service: TargetFundService = Depends(get_target_fund_service),
):
    return await service.toggle(fund_id=ctx.fund_id, target_fund_id=target_fund_id, user_id=ctx.user_id)


@router.delete("/{target_fund_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target_fund(
    target_fund_id: int,
    ctx: FundContext = Depends(require_fund_chairman),
    service: TargetFundService = Depends(get_target_fund_service),
):
    await service.delete(fund_id=ctx.fund_id, target_fund_id=target_fund_id, user_id=ctx.user_id)

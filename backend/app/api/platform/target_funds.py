from fastapi import APIRouter, Depends

from app.deps.fund import get_fund_context
from app.deps.services import get_target_fund_service
from app.schemas.member import FundContext
from app.schemas.target_fund import TargetFundDetailOut, TargetFundOut
from app.services.target_fund_service import TargetFundService

router = APIRouter(prefix="/funds/{fund_id}/target-funds", tags=["Platform • Target funds"])


@router.get("/", response_model=list[TargetFundOut])
async def list_target_funds(
    active_only: bool = False,
    ctx: FundContext = Depends(get_fund_context),
    service: TargetFundService = Depends(get_target_fund_service),
):
    return await service.list(fund_id=ctx.fund_id, active_only=active_only)


@router.get("/{target_fund_id}", response_model=TargetFundDetailOut)
async def get_target_fund(
    target_fund_id: int,
    ctx: FundContext = Depends(get_fund_context),
    service: TargetFundService = Depends(get_target_fund_service),
):
    return await service.get_detail(fund_id=ctx.fund_id, target_fund_id=target_fund_id)

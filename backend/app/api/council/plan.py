from fastapi import APIRouter, Depends, status

from app.deps.fund import require_fund_chairman, require_fund_council
from app.deps.services import get_plan_service
from app.schemas.member import FundContext
from app.schemas.plan import PlanRequestIn, PlanRequestOut
from app.services.plan_service import PlanService

router = APIRouter(prefix="/funds/{fund_id}/plan-requests", tags=["Council • Plan"])


@router.get("/", response_model=list[PlanRequestOut])
async def list_plan_requests(
    ctx: FundContext = Depends(require_fund_council),
    service: PlanService = Depends(get_plan_service),
):
    return await service.list_for_fund(fund_id=ctx.fund_id)


@router.post("/", response_model=PlanRequestOut, status_code=status.HTTP_201_CREATED)
async def create_plan_request(
    payload: PlanRequestIn,
    ctx: FundContext = Depends(require_fund_chairman),
    service: PlanService = Depends(get_plan_service),
):
    return await service.create_request(fund_id=ctx.fund_id, user_id=ctx.user_id, payload=payload)

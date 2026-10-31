from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from app.deps.fund import require_fund_chairman, require_fund_council
from app.deps.services import get_plan_service
from app.enums import PlanEnum
from app.schemas.member import FundContext
from app.schemas.plan import PlanRequestIn, PlanRequestOut
from app.schemas.pricing import PlanQuoteOut
from app.services.plan_service import PlanService

router = APIRouter(prefix="/funds/{fund_id}/plan-requests", tags=["Council • Plan"])


@router.get("/", response_model=list[PlanRequestOut])
async def list_plan_requests(
    ctx: FundContext = Depends(require_fund_council),
    service: PlanService = Depends(get_plan_service),
):
    return await service.list_for_fund(fund_id=ctx.fund_id)


@router.get("/quote", response_model=PlanQuoteOut)
async def quote_plan(
    plan: Literal[PlanEnum.pro, PlanEnum.max, PlanEnum.individual],
    months: int = Query(1, ge=1, le=12),
    promo_code: str | None = Query(None, max_length=30),
    ctx: FundContext = Depends(require_fund_chairman),
    service: PlanService = Depends(get_plan_service),
):
    return await service.quote(fund_id=ctx.fund_id, plan=plan, months=months, promo_code=promo_code)


@router.post("/", response_model=PlanRequestOut, status_code=status.HTTP_201_CREATED)
async def create_plan_request(
    payload: PlanRequestIn,
    background_tasks: BackgroundTasks,
    ctx: FundContext = Depends(require_fund_chairman),
    service: PlanService = Depends(get_plan_service),
):
    return await service.create_request(
        fund_id=ctx.fund_id, user_id=ctx.user_id, payload=payload, background_tasks=background_tasks
    )

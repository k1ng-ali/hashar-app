from fastapi import APIRouter, Depends, Query

from app.deps.auth import require_platform_admin
from app.deps.services import get_plan_service
from app.enums import PlanRequestStatusEnum
from app.schemas.plan import FundOutAdmin, FundPlanSetIn, PlanApproveIn, PlanRejectIn, PlanRequestOut
from app.schemas.user import CurrentUser
from app.services.plan_service import PlanService

router = APIRouter(tags=["Admin • Plans"])


@router.get("/plan-requests", response_model=list[PlanRequestOut])
async def list_plan_requests(
    status: PlanRequestStatusEnum | None = None,
    skip: int = 0,
    limit: int = Query(50, ge=1, le=100),
    user: CurrentUser = Depends(require_platform_admin),
    service: PlanService = Depends(get_plan_service),
):
    return await service.list_requests(status_filter=status, skip=skip, limit=limit)


@router.post("/plan-requests/{request_id}/approve", response_model=PlanRequestOut)
async def approve_plan_request(
    request_id: int,
    payload: PlanApproveIn,
    user: CurrentUser = Depends(require_platform_admin),
    service: PlanService = Depends(get_plan_service),
):
    return await service.approve(request_id=request_id, admin_id=user.id, payload=payload)


@router.post("/plan-requests/{request_id}/reject", response_model=PlanRequestOut)
async def reject_plan_request(
    request_id: int,
    payload: PlanRejectIn,
    user: CurrentUser = Depends(require_platform_admin),
    service: PlanService = Depends(get_plan_service),
):
    return await service.reject(request_id=request_id, admin_id=user.id, comment=payload.admin_comment)


# ─── Фонды ────────────────────────────────────────────────────────────────────


@router.get("/funds", response_model=list[FundOutAdmin])
async def list_funds(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=100),
    user: CurrentUser = Depends(require_platform_admin),
    service: PlanService = Depends(get_plan_service),
):
    return await service.list_funds(skip=skip, limit=limit)


@router.put("/funds/{fund_id}/plan", response_model=FundOutAdmin)
async def set_fund_plan(
    fund_id: int,
    payload: FundPlanSetIn,
    user: CurrentUser = Depends(require_platform_admin),
    service: PlanService = Depends(get_plan_service),
):
    return await service.set_plan(fund_id=fund_id, payload=payload)

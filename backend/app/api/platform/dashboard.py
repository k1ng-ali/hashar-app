from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.deps.fund import get_fund_context
from app.deps.services import get_account_service, get_dashboard_service
from app.schemas.account import RequisiteOut
from app.schemas.fund import AccountOut, FundSummaryOut, OperationOut
from app.schemas.member import FundContext
from app.services.account_service import AccountService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/funds/{fund_id}", tags=["Platform • Dashboard"])


@router.get("/summary", response_model=FundSummaryOut)
async def get_summary(
    ctx: FundContext = Depends(get_fund_context),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.summary(fund_id=ctx.fund_id)


@router.get("/operations", response_model=list[OperationOut])
async def list_operations(
    type: Literal["all", "income", "expense", "transfer"] = "all",
    limit: int = Query(10, ge=1, le=100),
    ctx: FundContext = Depends(get_fund_context),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.operations(fund_id=ctx.fund_id, type_filter=type, limit=limit)


@router.get("/accounts", response_model=list[AccountOut])
async def list_accounts(
    ctx: FundContext = Depends(get_fund_context),
    service: AccountService = Depends(get_account_service),
):
    return await service.list_accounts(fund_id=ctx.fund_id, active_only=True)


@router.get("/requisites", response_model=list[RequisiteOut])
async def list_requisites(
    ctx: FundContext = Depends(get_fund_context),
    service: AccountService = Depends(get_account_service),
):
    return await service.list_requisites(fund_id=ctx.fund_id, active_only=True)

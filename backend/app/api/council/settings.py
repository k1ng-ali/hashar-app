from fastapi import APIRouter, Depends, status

from app.deps.fund import require_fund_chairman, require_fund_council
from app.deps.services import get_account_service, get_fund_service
from app.enums import CurrencyEnum
from app.schemas.account import AccountCreateIn, RequisiteCreateIn, RequisiteOut
from app.schemas.fund import AccountOut, FundOut, FundUpdateIn
from app.schemas.member import FundContext
from app.services.account_service import AccountService
from app.services.fund_service import FundService

router = APIRouter(prefix="/funds/{fund_id}", tags=["Council • Settings"])


@router.patch("/settings", response_model=FundOut)
async def update_fund_settings(
    payload: FundUpdateIn,
    ctx: FundContext = Depends(require_fund_council),
    service: FundService = Depends(get_fund_service),
):
    # Валюту, тариф взноса и расчётный период меняет только председатель — проверка в сервисе
    return await service.update(ctx=ctx, payload=payload)


# ─── Валютные счета ───────────────────────────────────────────────────────────


@router.post("/accounts", response_model=list[AccountOut])
async def enable_account(
    payload: AccountCreateIn,
    ctx: FundContext = Depends(require_fund_chairman),
    service: AccountService = Depends(get_account_service),
):
    return await service.enable_currency(fund_id=ctx.fund_id, currency=payload.currency, user_id=ctx.user_id)


@router.post("/accounts/{currency}/disable", response_model=list[AccountOut])
async def disable_account(
    currency: CurrencyEnum,
    ctx: FundContext = Depends(require_fund_chairman),
    service: AccountService = Depends(get_account_service),
):
    return await service.disable_currency(fund_id=ctx.fund_id, currency=currency, user_id=ctx.user_id)


# ─── Реквизиты ────────────────────────────────────────────────────────────────


@router.get("/requisites", response_model=list[RequisiteOut])
async def list_requisites(
    ctx: FundContext = Depends(require_fund_council),
    service: AccountService = Depends(get_account_service),
):
    return await service.list_requisites(fund_id=ctx.fund_id)


@router.post("/requisites", response_model=RequisiteOut, status_code=status.HTTP_201_CREATED)
async def create_requisite(
    payload: RequisiteCreateIn,
    ctx: FundContext = Depends(require_fund_chairman),
    service: AccountService = Depends(get_account_service),
):
    return await service.create_requisite(fund_id=ctx.fund_id, payload=payload, user_id=ctx.user_id)


@router.post("/requisites/{requisite_id}/toggle", response_model=RequisiteOut)
async def toggle_requisite(
    requisite_id: int,
    ctx: FundContext = Depends(require_fund_chairman),
    service: AccountService = Depends(get_account_service),
):
    return await service.toggle_requisite(fund_id=ctx.fund_id, requisite_id=requisite_id, user_id=ctx.user_id)


@router.delete("/requisites/{requisite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requisite(
    requisite_id: int,
    ctx: FundContext = Depends(require_fund_chairman),
    service: AccountService = Depends(get_account_service),
):
    await service.delete_requisite(fund_id=ctx.fund_id, requisite_id=requisite_id, user_id=ctx.user_id)

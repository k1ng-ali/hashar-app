from fastapi import APIRouter, Depends, Query, status

from app.deps.fund import require_fund_council
from app.deps.services import get_account_service
from app.schemas.account import TransferCreateIn, TransferOut
from app.schemas.member import FundContext
from app.services.account_service import AccountService

router = APIRouter(prefix="/funds/{fund_id}/transfers", tags=["Council • Transfers"])


@router.get("/", response_model=list[TransferOut])
async def list_transfers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    ctx: FundContext = Depends(require_fund_council),
    service: AccountService = Depends(get_account_service),
):
    return await service.list_transfers(fund_id=ctx.fund_id, skip=skip, limit=limit)


@router.post("/", response_model=TransferOut, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    payload: TransferCreateIn,
    ctx: FundContext = Depends(require_fund_council),
    service: AccountService = Depends(get_account_service),
):
    # Каждое движение по счетам автоматически публикуется в объявлениях
    return await service.create_transfer(fund_id=ctx.fund_id, user_id=ctx.user_id, payload=payload)

from fastapi import APIRouter, Depends, Query, status

from app.deps.fund import get_fund_context
from app.deps.services import get_contribution_service, get_member_service
from app.enums import ContributionStatusEnum
from app.schemas.balance import ResidentBalanceOut
from app.schemas.contribution import ContributionCreateIn, ContributionOut
from app.schemas.member import FundContext
from app.services.contribution_service import ContributionService
from app.services.member_service import MemberService

router = APIRouter(prefix="/funds/{fund_id}/contributions", tags=["Platform • Contributions"])


@router.get("/my", response_model=list[ContributionOut])
async def list_my_contributions(
    status_filter: ContributionStatusEnum | None = Query(None, alias="status"),
    skip: int = 0,
    limit: int = Query(50, ge=1, le=100),
    ctx: FundContext = Depends(get_fund_context),
    service: ContributionService = Depends(get_contribution_service),
):
    return await service.list_my(
        fund_id=ctx.fund_id,
        user_id=ctx.user_id,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get("/my/balance", response_model=ResidentBalanceOut)
async def get_my_balance(
    ctx: FundContext = Depends(get_fund_context),
    service: MemberService = Depends(get_member_service),
):
    return await service.get_balance(fund_id=ctx.fund_id, user_id=ctx.user_id)


@router.post("/", response_model=ContributionOut, status_code=status.HTTP_201_CREATED)
async def create_contribution(
    payload: ContributionCreateIn,
    ctx: FundContext = Depends(get_fund_context),
    service: ContributionService = Depends(get_contribution_service),
):
    return await service.create(fund_id=ctx.fund_id, user_id=ctx.user_id, payload=payload)

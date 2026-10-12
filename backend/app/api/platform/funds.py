from fastapi import APIRouter, Depends, Query, status

from app.deps.auth import get_current_user
from app.deps.fund import get_fund_context
from app.deps.services import get_fund_service, get_plan_service
from app.schemas.fund import FundCreateIn, FundOut, FundPublicOut, MyFundOut
from app.schemas.member import FundContext, JoinIn, MemberOut
from app.schemas.plan import PlanOptionOut
from app.schemas.user import CurrentUser
from app.services.fund_service import FundService
from app.services.plan_service import PlanService

router = APIRouter(prefix="/funds", tags=["Platform • Funds"])


@router.post("/", response_model=FundOut, status_code=status.HTTP_201_CREATED)
async def create_fund(
    payload: FundCreateIn,
    user: CurrentUser = Depends(get_current_user),
    service: FundService = Depends(get_fund_service),
):
    return await service.create(user_id=user.id, payload=payload)


@router.get("/my", response_model=list[MyFundOut])
async def list_my_funds(
    user: CurrentUser = Depends(get_current_user),
    service: FundService = Depends(get_fund_service),
):
    return await service.list_my(user_id=user.id)


@router.get("/search", response_model=list[FundPublicOut])
async def search_funds(
    q: str = Query(min_length=2, max_length=150),
    user: CurrentUser = Depends(get_current_user),
    service: FundService = Depends(get_fund_service),
):
    return await service.search(user_id=user.id, query=q)


@router.get("/by-code/{code}", response_model=FundPublicOut)
async def get_fund_by_code(
    code: str,
    user: CurrentUser = Depends(get_current_user),
    service: FundService = Depends(get_fund_service),
):
    return await service.get_by_code(user_id=user.id, code=code)


@router.get("/plans", response_model=list[PlanOptionOut])
async def list_plans(
    user: CurrentUser = Depends(get_current_user),
    service: PlanService = Depends(get_plan_service),
):
    return service.catalog()


# ─── Вступление ───────────────────────────────────────────────────────────────


@router.post("/{fund_id}/join", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
async def join_fund(
    fund_id: int,
    payload: JoinIn,
    user: CurrentUser = Depends(get_current_user),
    service: FundService = Depends(get_fund_service),
):
    return await service.join(fund_id=fund_id, user_id=user.id, payload=payload)


@router.delete("/{fund_id}/join", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_join_request(
    fund_id: int,
    user: CurrentUser = Depends(get_current_user),
    service: FundService = Depends(get_fund_service),
):
    await service.cancel_request(fund_id=fund_id, user_id=user.id)


# ─── Участникам фонда ─────────────────────────────────────────────────────────


@router.get("/{fund_id}", response_model=FundOut)
async def get_fund(
    ctx: FundContext = Depends(get_fund_context),
    service: FundService = Depends(get_fund_service),
):
    return await service.get(ctx=ctx)


@router.post("/{fund_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_fund(
    fund_id: int,
    user: CurrentUser = Depends(get_current_user),
    service: FundService = Depends(get_fund_service),
):
    # Без проверки активного членства: выйти может и заблокированный
    await service.leave(fund_id=fund_id, user_id=user.id)

from fastapi import APIRouter, Depends

from app.deps.fund import require_fund_chairman, require_fund_council
from app.deps.services import get_member_service
from app.enums import MemberStatusEnum
from app.schemas.member import (
    ChairmanTransferIn,
    FundContext,
    MemberOut,
    MemberOutCouncil,
    MemberRoleUpdateIn,
    MemberStatusUpdateIn,
)
from app.services.member_service import MemberService

router = APIRouter(prefix="/funds/{fund_id}/members", tags=["Council • Members"])


@router.get("/", response_model=list[MemberOutCouncil])
async def list_members(
    status: MemberStatusEnum | None = None,
    only_debtors: bool = False,
    ctx: FundContext = Depends(require_fund_council),
    service: MemberService = Depends(get_member_service),
):
    return await service.list_members(fund_id=ctx.fund_id, status_filter=status, only_debtors=only_debtors)


@router.post("/{member_id}/approve", response_model=MemberOut)
async def approve_member(
    member_id: int,
    ctx: FundContext = Depends(require_fund_council),
    service: MemberService = Depends(get_member_service),
):
    return await service.approve(fund_id=ctx.fund_id, member_id=member_id, reviewer_id=ctx.user_id)


@router.post("/{member_id}/reject", response_model=MemberOut)
async def reject_member(
    member_id: int,
    ctx: FundContext = Depends(require_fund_council),
    service: MemberService = Depends(get_member_service),
):
    return await service.reject(fund_id=ctx.fund_id, member_id=member_id, reviewer_id=ctx.user_id)


@router.patch("/{member_id}/status", response_model=MemberOut)
async def update_member_status(
    member_id: int,
    payload: MemberStatusUpdateIn,
    ctx: FundContext = Depends(require_fund_council),
    service: MemberService = Depends(get_member_service),
):
    return await service.set_status(
        fund_id=ctx.fund_id,
        member_id=member_id,
        new_status=payload.status,
        actor_id=ctx.user_id,
    )


@router.patch("/{member_id}/role", response_model=MemberOut)
async def update_member_role(
    member_id: int,
    payload: MemberRoleUpdateIn,
    ctx: FundContext = Depends(require_fund_chairman),
    service: MemberService = Depends(get_member_service),
):
    return await service.set_role(fund_id=ctx.fund_id, member_id=member_id, role=payload.role, actor_id=ctx.user_id)


@router.post("/transfer-chairman", response_model=MemberOut)
async def transfer_chairman(
    payload: ChairmanTransferIn,
    ctx: FundContext = Depends(require_fund_chairman),
    service: MemberService = Depends(get_member_service),
):
    return await service.transfer_chairman(
        fund_id=ctx.fund_id,
        member_id=payload.member_id,
        actor_member_id=ctx.member_id,
    )

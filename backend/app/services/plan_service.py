from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import effective_plan, member_limit, plan_price
from app.enums import PLAN_MEMBER_LIMITS, PLAN_PRICES_TJS, PlanEnum, PlanRequestStatusEnum
from app.models.fund import Fund
from app.models.plan_request import PlanRequest
from app.repositories.fund_repo import FundRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.plan_request_repo import PlanRequestRepository
from app.schemas.fund import PlanInfoOut
from app.schemas.plan import (
    FundCouncilMemberOut,
    FundOutAdmin,
    FundPlanSetIn,
    PlanApproveIn,
    PlanOptionOut,
    PlanRequestIn,
    PlanRequestOut,
)

# Длина оплаченного месяца тарифа
PLAN_MONTH = timedelta(days=30)


def plan_request_out(request: PlanRequest) -> PlanRequestOut:
    return PlanRequestOut(
        id=request.id,
        fund_id=request.fund_id,
        fund_name=request.fund.name,
        plan=request.plan,
        months=request.months,
        status=request.status,
        contact=request.contact,
        comment=request.comment,
        admin_comment=request.admin_comment,
        requested_by_name=request.requested_by.full_name if request.requested_by else None,
        reviewed_at=request.reviewed_at,
        created_at=request.created_at,
    )


class PlanService:
    """Тарифы платформы: лимиты участников, заявки председателей, решения админа платформы."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PlanRequestRepository(db=db)
        self.fund_repo = FundRepository(db=db)
        self.member_repo = MemberRepository(db=db)

    # ─── Лимиты ────────────────────────────────────────────────────────────────

    @staticmethod
    def catalog() -> list[PlanOptionOut]:
        return [
            PlanOptionOut(plan=plan, member_limit=PLAN_MEMBER_LIMITS[plan], price_tjs=PLAN_PRICES_TJS[plan])
            for plan in PlanEnum
        ]

    async def info(self, fund: Fund) -> PlanInfoOut:
        plan = effective_plan(fund)
        return PlanInfoOut(
            plan=fund.plan,
            effective_plan=plan,
            expires_at=fund.plan_expires_at,
            member_limit=member_limit(fund),
            members_count=await self.member_repo.count_active(fund.id),
            price_tjs=plan_price(plan),
        )

    async def ensure_capacity(self, fund: Fund) -> None:
        """409, если в фонде уже максимум участников по тарифу."""
        limit = member_limit(fund)
        if limit is not None and await self.member_repo.count_active(fund.id) >= limit:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member limit reached for the plan")

    # ─── Председатель ──────────────────────────────────────────────────────────

    async def create_request(self, fund_id: int, user_id: int, payload: PlanRequestIn) -> PlanRequestOut:
        if await self.repo.has_pending(fund_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Plan request is already pending")

        request = await self.repo.create(
            fund_id=fund_id,
            plan=payload.plan.value,
            months=payload.months,
            contact=payload.contact.strip(),
            comment=payload.comment,
            requested_by_id=user_id,
        )
        await self.db.commit()
        return plan_request_out(request)

    async def list_for_fund(self, fund_id: int) -> list[PlanRequestOut]:
        return [plan_request_out(r) for r in await self.repo.list(fund_id=fund_id, limit=20)]

    # ─── Админ платформы ───────────────────────────────────────────────────────

    async def list_requests(
        self,
        status_filter: PlanRequestStatusEnum | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[PlanRequestOut]:
        items = await self.repo.list(status=status_filter.value if status_filter else None, skip=skip, limit=limit)
        return [plan_request_out(r) for r in items]

    async def approve(self, request_id: int, admin_id: int, payload: PlanApproveIn) -> PlanRequestOut:
        request = await self._get_pending_or_error(request_id)
        fund = await self.fund_repo.get(request.fund_id, for_update=True)

        months = payload.months or request.months
        now = datetime.now(timezone.utc)
        # Продление: считаем от текущей даты окончания, если тот же тариф ещё действует
        start = (
            fund.plan_expires_at
            if fund.plan == request.plan and fund.plan_expires_at and fund.plan_expires_at > now
            else now
        )

        fund.plan = request.plan
        fund.plan_expires_at = start + PLAN_MONTH * months
        if request.plan == PlanEnum.individual.value:
            fund.member_limit = payload.member_limit

        self._close(request, admin_id, PlanRequestStatusEnum.approved, payload.admin_comment)
        await self.db.commit()
        return plan_request_out(await self.repo.get(request_id))

    async def reject(self, request_id: int, admin_id: int, comment: str) -> PlanRequestOut:
        request = await self._get_pending_or_error(request_id)
        self._close(request, admin_id, PlanRequestStatusEnum.rejected, comment)
        await self.db.commit()
        return plan_request_out(await self.repo.get(request_id))

    async def list_funds(self, skip: int = 0, limit: int = 50) -> list[FundOutAdmin]:
        funds = await self.fund_repo.list_all(skip=skip, limit=limit)
        return await self._funds_admin_out(funds)

    async def set_plan(self, fund_id: int, payload: FundPlanSetIn) -> FundOutAdmin:
        fund = await self.fund_repo.get(fund_id, for_update=True)
        if not fund:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fund not found")

        fund.plan = payload.plan.value
        fund.plan_expires_at = None if payload.plan == PlanEnum.free else payload.expires_at
        fund.member_limit = payload.member_limit if payload.plan == PlanEnum.individual else None
        await self.db.commit()
        return (await self._funds_admin_out([fund]))[0]

    # ─── Helpers ───────────────────────────────────────────────────────────────

    async def _get_pending_or_error(self, request_id: int) -> PlanRequest:
        request = await self.repo.get(request_id, for_update=True)
        if not request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan request not found")
        if request.status != PlanRequestStatusEnum.pending.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Plan request already reviewed")
        return request

    @staticmethod
    def _close(request: PlanRequest, admin_id: int, new_status: PlanRequestStatusEnum, comment: str | None) -> None:
        request.status = new_status.value
        request.admin_comment = comment
        request.reviewed_by_id = admin_id
        request.reviewed_at = datetime.now(timezone.utc)

    async def _funds_admin_out(self, funds: list[Fund]) -> list[FundOutAdmin]:
        fund_ids = [f.id for f in funds]
        counts = await self.member_repo.count_active_by_funds(fund_ids)
        councils = await self.member_repo.list_council_by_funds(fund_ids)
        return [
            FundOutAdmin(
                id=fund.id,
                name=fund.name,
                code=fund.code,
                address=fund.address,
                plan=fund.plan,
                effective_plan=effective_plan(fund),
                plan_expires_at=fund.plan_expires_at,
                member_limit=member_limit(fund),
                members_count=counts.get(fund.id, 0),
                council=[
                    FundCouncilMemberOut(
                        user_id=m.user_id,
                        full_name=m.user.full_name,
                        role=m.role,
                        phone=m.user.phone,
                        email=m.user.email,
                        address_unit=m.address_unit,
                    )
                    for m in councils.get(fund.id, [])
                ],
                created_at=fund.created_at,
            )
            for fund in funds
        ]

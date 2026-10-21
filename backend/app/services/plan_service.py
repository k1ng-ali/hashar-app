from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import (
    PLAN_MONTH,
    blocks_at,
    carryover,
    effective_plan,
    free_limit,
    is_extension,
    lapse_state,
    member_limit,
    plan_price,
)
from app.enums import (
    COUNCIL_ROLES,
    PLAN_MEMBER_LIMITS,
    PLAN_PRICES_TJS,
    FundRoleEnum,
    LapseEnum,
    PlanEnum,
    PlanRequestStatusEnum,
)
from app.models.fund import Fund
from app.models.plan_request import PlanRequest
from app.repositories.audit_repo import AuditRepository
from app.repositories.fund_repo import FundRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.notice_repo import NoticeRepository
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


def plan_request_out(request: PlanRequest) -> PlanRequestOut:
    preview = None
    if request.status == PlanRequestStatusEnum.pending.value:
        new_price = plan_price(PlanEnum(request.plan))
        if not is_extension(request.fund, PlanEnum(request.plan), new_price, datetime.now(timezone.utc)):
            preview = carryover(request.fund, new_price)
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
        carryover_tjs=preview.value_tjs if preview else None,
        carryover_days=round(preview.extra / DAY) if preview and preview.extra is not None else None,
    )


DAY = PLAN_MONTH / 30


class PlanService:
    """Тарифы платформы: лимиты участников, заявки председателей, решения админа платформы."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PlanRequestRepository(db=db)
        self.fund_repo = FundRepository(db=db)
        self.member_repo = MemberRepository(db=db)
        self.audit = AuditRepository(db=db)
        self.notices = NoticeRepository(db=db)

    # ─── Лимиты ────────────────────────────────────────────────────────────────

    @staticmethod
    def catalog() -> list[PlanOptionOut]:
        return [
            PlanOptionOut(plan=plan, member_limit=PLAN_MEMBER_LIMITS[plan], price_tjs=PLAN_PRICES_TJS[plan])
            for plan in PlanEnum
        ]

    async def info(self, fund: Fund, user_id: int | None = None, role: FundRoleEnum | None = None) -> PlanInfoOut:
        plan = effective_plan(fund)
        members_count = await self.member_repo.count_active(fund.id)
        lapse = lapse_state(fund)
        blocked = lapse == LapseEnum.lapsed and members_count > free_limit()
        return PlanInfoOut(
            plan=fund.plan,
            effective_plan=plan,
            expires_at=fund.plan_expires_at,
            member_limit=member_limit(fund),
            members_count=members_count,
            price_tjs=(fund.plan_price or plan_price(plan)) if plan != PlanEnum.free else 0,
            remaining_tjs=remaining.value_tjs if (remaining := carryover(fund, None)) else None,
            lapse=lapse,
            blocks_at=blocks_at(fund) if lapse != LapseEnum.none else None,
            over_free_limit=members_count > free_limit(),
            contributions_blocked=blocked,
            can_contribute=not blocked or (user_id is not None and await self._in_free_council(fund, user_id, role)),
        )

    # ─── Взносы после окончания тарифа ─────────────────────────────────────────

    async def ensure_can_contribute(self, fund: Fund, user_id: int, role: FundRoleEnum | None) -> None:
        """403, если тариф не продлён после льготного срока, а пользователь не входит в 10 членов совета."""
        if lapse_state(fund) != LapseEnum.lapsed:
            return
        if await self.member_repo.count_active(fund.id) <= free_limit():
            return
        if not await self._in_free_council(fund, user_id, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Fund plan expired: contributions are blocked"
            )

    async def _in_free_council(self, fund: Fund, user_id: int, role: FundRoleEnum | None) -> bool:
        """Председатель и самые ранние администраторы в пределах лимита Free — раздача прав лимит не обходит."""
        if role not in COUNCIL_ROLES:
            return False
        return user_id in await self.member_repo.first_council_user_ids(fund.id, free_limit())

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

        new_plan = PlanEnum(request.plan)
        new_price = self._price_for(new_plan, payload.monthly_price)
        months = payload.months or request.months
        now = datetime.now(timezone.utc)

        details = {"request_id": request.id, "months": months}
        if is_extension(fund, new_plan, new_price, now):
            # Продление того же тарифа — от текущей даты окончания
            start = fund.plan_expires_at
        else:
            # Другой тариф: оплаченный остаток не сгорает, а докупает дни нового по его цене
            rest = carryover(fund, new_price, now)
            start = now + rest.extra if rest else now
            if rest:
                details.update(carryover_tjs=rest.value_tjs, carryover_days=round(rest.extra / DAY, 1))

        fund.plan = new_plan.value
        fund.plan_price = new_price
        fund.plan_expires_at = start + PLAN_MONTH * months
        if new_plan == PlanEnum.individual:
            fund.member_limit = payload.member_limit

        self._close(request, admin_id, PlanRequestStatusEnum.approved, payload.admin_comment)
        self._audit_plan(fund, "plan.approve", admin_id, **details)
        self.notices.add(
            fund_id=fund.id,
            kind="plan_approved",
            details={
                "plan": fund.plan,
                "expires_at": fund.plan_expires_at.isoformat(),
                "comment": payload.admin_comment,
            },
            author_id=admin_id,
        )
        await self.db.commit()
        return plan_request_out(await self.repo.get(request_id))

    async def reject(self, request_id: int, admin_id: int, comment: str) -> PlanRequestOut:
        request = await self._get_pending_or_error(request_id)
        self._close(request, admin_id, PlanRequestStatusEnum.rejected, comment)
        # Совет видит отказ и причину в окне уведомлений
        self.notices.add(
            fund_id=request.fund_id,
            kind="plan_rejected",
            details={"plan": request.plan, "months": request.months, "reason": comment},
            author_id=admin_id,
        )
        await self.db.commit()
        return plan_request_out(await self.repo.get(request_id))

    async def list_funds(self, skip: int = 0, limit: int = 50) -> list[FundOutAdmin]:
        funds = await self.fund_repo.list_all(skip=skip, limit=limit)
        return await self._funds_admin_out(funds)

    async def set_plan(self, fund_id: int, payload: FundPlanSetIn, admin_id: int) -> FundOutAdmin:
        fund = await self.fund_repo.get(fund_id, for_update=True)
        if not fund:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fund not found")

        fund.plan = payload.plan.value
        fund.plan_price = (
            None if payload.plan == PlanEnum.free else self._price_for(payload.plan, payload.monthly_price)
        )
        fund.plan_expires_at = None if payload.plan == PlanEnum.free else payload.expires_at
        fund.member_limit = payload.member_limit if payload.plan == PlanEnum.individual else None
        self._audit_plan(fund, "plan.set", admin_id)
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

    def _audit_plan(self, fund: Fund, action: str, admin_id: int, **details) -> None:
        self.audit.add(
            fund_id=fund.id,
            actor_id=admin_id,
            action=action,
            entity="fund",
            entity_id=fund.id,
            details={
                "plan": fund.plan,
                "expires_at": fund.plan_expires_at.isoformat() if fund.plan_expires_at else None,
                "member_limit": fund.member_limit,
                "price": fund.plan_price,
                **details,
            },
        )

    @staticmethod
    def _price_for(plan: PlanEnum, monthly_price: int | None) -> int:
        """Цена тарифа за месяц: из каталога, у individual — договорная от админа."""
        price = plan_price(plan)
        if price is not None:
            return price
        if not monthly_price:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="monthly_price is required for this plan"
            )
        return monthly_price

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

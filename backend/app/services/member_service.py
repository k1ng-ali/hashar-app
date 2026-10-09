from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.finance import calculate_balance, current_period, period_of
from app.enums import BalanceStatusEnum, ContributionStatusEnum, FundRoleEnum, MemberStatusEnum
from app.models.fund import Fund
from app.models.member import FundMember
from app.repositories.contribution_repo import ContributionRepository
from app.repositories.fund_repo import FundRepository
from app.repositories.member_repo import MemberRepository
from app.schemas.balance import ResidentBalanceOut
from app.schemas.member import MemberOut, MemberOutCouncil
from app.schemas.report import DebtorOut
from app.services.plan_service import PlanService

APPROVED = ContributionStatusEnum.approved.value
PENDING = ContributionStatusEnum.pending.value
ACTIVE = MemberStatusEnum.active.value


def member_out(member: FundMember) -> MemberOut:
    return MemberOut(
        id=member.id,
        user_id=member.user_id,
        full_name=member.user.full_name,
        phone=member.user.phone,
        email=member.user.email,
        avatar_url=member.user.avatar_url,
        role=member.role,
        status=member.status,
        address_unit=member.address_unit,
        message=member.message,
        joined_at=member.joined_at,
        created_at=member.created_at,
    )


class MemberService:
    """Участники фонда: заявки на вступление, роли, сальдо ежемесячных взносов."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MemberRepository(db=db)
        self.fund_repo = FundRepository(db=db)
        self.contribution_repo = ContributionRepository(db=db)
        self.plans = PlanService(db=db)

    # ─── Сальдо ────────────────────────────────────────────────────────────────

    async def get_balance(self, fund_id: int, user_id: int) -> ResidentBalanceOut:
        fund = await self._get_fund(fund_id)
        member = await self.repo.get_by_user(fund_id, user_id)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        return (await self._balances_for(fund, [member]))[user_id]

    async def list_debtors(self, fund_id: int) -> list[DebtorOut]:
        fund = await self._get_fund(fund_id)
        members = await self.repo.list(fund_id, status=ACTIVE)
        balances = await self._balances_for(fund, members)
        return [
            DebtorOut(
                member_id=m.id,
                user_id=m.user_id,
                full_name=m.user.full_name,
                address_unit=m.address_unit,
                phone=m.user.phone,
                debt_amount=balances[m.user_id].debt_amount,
                currency=fund.base_currency,
                debt_months_count=balances[m.user_id].debt_months_count,
                unpaid_periods=balances[m.user_id].unpaid_periods,
            )
            for m in members
            if balances[m.user_id].status == BalanceStatusEnum.debt
        ]

    # ─── Совет: реестр и заявки ────────────────────────────────────────────────

    async def list_members(
        self,
        fund_id: int,
        status_filter: MemberStatusEnum | None = None,
        only_debtors: bool = False,
    ) -> list[MemberOutCouncil]:
        fund = await self._get_fund(fund_id)
        members = await self.repo.list(fund_id, status=status_filter.value if status_filter else None)
        balances = await self._balances_for(fund, [m for m in members if m.status == ACTIVE])

        items = [
            MemberOutCouncil(
                **member_out(m).model_dump(), balance=balances.get(m.user_id) if m.status == ACTIVE else None
            )
            for m in members
        ]
        if only_debtors:
            items = [i for i in items if i.balance and i.balance.status == BalanceStatusEnum.debt]
        return items

    async def approve(self, fund_id: int, member_id: int, reviewer_id: int) -> MemberOut:
        member = await self._get_or_404(fund_id, member_id, for_update=True)
        if member.status != MemberStatusEnum.pending.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request is not pending")

        fund = await self.fund_repo.get(fund_id, for_update=True)
        await self.plans.ensure_capacity(fund)

        member.status = ACTIVE
        member.reviewed_by_id = reviewer_id
        member.joined_at = datetime.now(timezone.utc)
        await self.db.commit()
        return member_out(member)

    async def reject(self, fund_id: int, member_id: int, reviewer_id: int) -> MemberOut:
        member = await self._get_or_404(fund_id, member_id, for_update=True)
        if member.status != MemberStatusEnum.pending.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request is not pending")

        member.status = MemberStatusEnum.rejected.value
        member.reviewed_by_id = reviewer_id
        await self.db.commit()
        return member_out(member)

    async def set_status(self, fund_id: int, member_id: int, new_status: MemberStatusEnum, actor_id: int) -> MemberOut:
        member = await self._get_or_404(fund_id, member_id, for_update=True)
        self._ensure_not_self_or_chairman(member, actor_id)
        if member.status not in (ACTIVE, MemberStatusEnum.blocked.value):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member is not active or blocked")

        if new_status == MemberStatusEnum.active and member.status != ACTIVE:
            # Разблокировка снова занимает место в лимите тарифа
            await self.plans.ensure_capacity(await self.fund_repo.get(fund_id, for_update=True))

        member.status = new_status.value
        await self.db.commit()
        return member_out(member)

    async def set_role(self, fund_id: int, member_id: int, role: FundRoleEnum, actor_id: int) -> MemberOut:
        member = await self._get_or_404(fund_id, member_id, for_update=True)
        self._ensure_not_self_or_chairman(member, actor_id)
        if member.status != ACTIVE:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member is not active")

        member.role = role.value
        await self.db.commit()
        return member_out(member)

    async def transfer_chairman(self, fund_id: int, member_id: int, actor_member_id: int) -> MemberOut:
        """Передача прав председателя. Бывший председатель остаётся в совете (admin)."""
        if member_id == actor_member_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already the chairman")

        target = await self._get_or_404(fund_id, member_id, for_update=True)
        if target.status != ACTIVE:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member is not active")
        current = await self._get_or_404(fund_id, actor_member_id, for_update=True)

        current.role = FundRoleEnum.admin.value
        target.role = FundRoleEnum.chairman.value
        await self.db.commit()
        return member_out(target)

    # ─── Helpers ───────────────────────────────────────────────────────────────

    async def _balances_for(self, fund: Fund, members: list[FundMember]) -> dict[int, ResidentBalanceOut]:
        user_ids = [m.user_id for m in members]
        sums = await self.contribution_repo.monthly_sums_by_user(
            fund.id, currency=fund.base_currency, user_ids=user_ids
        )
        today = current_period()
        result = {}
        for member in members:
            # Начисления идут с месяца вступления, но не раньше старта фонда
            joined = period_of(member.joined_at) if member.joined_at else fund.start_period
            result[member.user_id] = calculate_balance(
                paid=sums.get(member.user_id, {}).get(APPROVED, 0),
                pending=sums.get(member.user_id, {}).get(PENDING, 0),
                rate=fund.monthly_rate,
                start_period=max(fund.start_period, joined),
                today_period=today,
                currency=fund.base_currency,
            )
        return result

    async def _get_fund(self, fund_id: int) -> Fund:
        fund = await self.fund_repo.get(fund_id)
        if not fund:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fund not found")
        return fund

    async def _get_or_404(self, fund_id: int, member_id: int, for_update: bool = False) -> FundMember:
        member = await self.repo.get(fund_id, member_id, for_update=for_update)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        return member

    @staticmethod
    def _ensure_not_self_or_chairman(member: FundMember, actor_id: int) -> None:
        if member.user_id == actor_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot change yourself")
        if member.role == FundRoleEnum.chairman.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change the chairman")

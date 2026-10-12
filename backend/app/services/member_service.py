from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.finance import (
    RateSchedule,
    calculate_balance,
    current_period,
    period_of,
    periods_range,
    rate_at,
    shift_period,
)
from app.enums import BalanceStatusEnum, ContributionStatusEnum, FundRoleEnum, MemberStatusEnum
from app.models.fund import Fund
from app.models.member import FundMember
from app.repositories.accrual_pause_repo import AccrualPauseRepository
from app.repositories.audit_repo import AuditRepository
from app.repositories.contribution_repo import ContributionRepository
from app.repositories.fund_rate_repo import FundRateRepository
from app.repositories.fund_repo import FundRepository
from app.repositories.member_repo import MemberRepository
from app.schemas.balance import ResidentBalanceOut
from app.schemas.member import AbsenceOut, MemberOut, MemberOutCouncil
from app.schemas.report import DebtorOut
from app.services.plan_service import PlanService

APPROVED = ContributionStatusEnum.approved.value
PENDING = ContributionStatusEnum.pending.value
ACTIVE = MemberStatusEnum.active.value
BLOCKED = MemberStatusEnum.blocked.value


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
        left_at=member.left_at,
        blocked_at=member.blocked_at,
        created_at=member.created_at,
    )


def away_since(member: FundMember) -> datetime | None:
    """С какого момента участник отсутствует: вышел или заблокирован (что раньше)."""
    dates = [d for d in (member.left_at, member.blocked_at) if d is not None]
    return min(dates) if dates else None


def absence_periods(since: datetime, today: str) -> list[str]:
    """
    Месяцы отсутствия, о которых решает совет: строго между месяцем ухода и текущим.

    Месяц ухода начислен — участник в нём был; текущий начисляется, как у любого
    нового участника.
    """
    return periods_range(shift_period(period_of(since), 1), shift_period(today, -1))


class MemberService:
    """Участники фонда: заявки на вступление, роли, сальдо ежемесячных взносов."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MemberRepository(db=db)
        self.fund_repo = FundRepository(db=db)
        self.rate_repo = FundRateRepository(db=db)
        self.contribution_repo = ContributionRepository(db=db)
        self.pause_repo = AccrualPauseRepository(db=db)
        self.audit = AuditRepository(db=db)
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
        # Сальдо есть у всех, кто уже был участником (в т. ч. у вышедших и возвращающихся)
        with_history = [m for m in members if m.joined_at is not None and m.status != MemberStatusEnum.rejected.value]
        balances = await self._balances_for(fund, with_history)
        schedule = await self.rate_repo.schedule(fund.id)

        items = [
            MemberOutCouncil(
                **member_out(m).model_dump(),
                balance=balances.get(m.user_id) if m in with_history else None,
                absence=self._absence(fund, m, schedule, balances.get(m.user_id)),
            )
            for m in members
        ]
        if only_debtors:
            items = [i for i in items if i.balance and i.balance.status == BalanceStatusEnum.debt]
        return items

    async def approve(
        self,
        fund_id: int,
        member_id: int,
        reviewer_id: int,
        accrue_absence: bool | None = None,
    ) -> MemberOut:
        member = await self._get_or_404(fund_id, member_id, for_update=True)
        if member.status != MemberStatusEnum.pending.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request is not pending")

        fund = await self.fund_repo.get(fund_id, for_update=True)
        await self.plans.ensure_capacity(fund)

        since = away_since(member)
        if since is not None:
            # Возвращение: совет обязан явно решить судьбу периода отсутствия
            if accrue_absence is None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Absence decision required")
            await self._decide_absence(member, since, accrue_absence, "left", reviewer_id)

        member.status = ACTIVE
        member.reviewed_by_id = reviewer_id
        # Возвращающийся сохраняет дату первого вступления — долг до ухода остаётся
        member.joined_at = member.joined_at or datetime.now(timezone.utc)
        member.left_at = None
        member.blocked_at = None
        self._audit(member, "member.approve", reviewer_id, accrue_absence=accrue_absence)
        await self.db.commit()
        return member_out(member)

    async def reject(self, fund_id: int, member_id: int, reviewer_id: int) -> MemberOut:
        member = await self._get_or_404(fund_id, member_id, for_update=True)
        if member.status != MemberStatusEnum.pending.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request is not pending")

        member.status = MemberStatusEnum.rejected.value
        member.reviewed_by_id = reviewer_id
        self._audit(member, "member.reject", reviewer_id)
        await self.db.commit()
        return member_out(member)

    async def set_status(
        self,
        fund_id: int,
        member_id: int,
        new_status: MemberStatusEnum,
        actor_id: int,
        accrue_absence: bool | None = None,
    ) -> MemberOut:
        member = await self._get_or_404(fund_id, member_id, for_update=True)
        self._ensure_not_self_or_chairman(member, actor_id)
        if member.status not in (ACTIVE, BLOCKED):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member is not active or blocked")
        if member.status == new_status.value:
            return member_out(member)

        if new_status == MemberStatusEnum.blocked:
            member.status = BLOCKED
            member.blocked_at = datetime.now(timezone.utc)
        elif member.left_at is not None:
            # Вышел во время блокировки: просто снимаем блок — решение о периоде
            # отсутствия совет примет, когда участник подаст заявку на возвращение
            member.status = MemberStatusEnum.left.value
        else:
            if accrue_absence is None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Absence decision required")
            # Разблокировка снова занимает место в лимите тарифа
            await self.plans.ensure_capacity(await self.fund_repo.get(fund_id, for_update=True))
            if member.blocked_at is not None:
                await self._decide_absence(member, member.blocked_at, accrue_absence, "blocked", actor_id)
            member.status = ACTIVE
            member.blocked_at = None

        self._audit(member, f"member.{new_status.value}", actor_id, accrue_absence=accrue_absence)
        await self.db.commit()
        return member_out(member)

    async def set_role(self, fund_id: int, member_id: int, role: FundRoleEnum, actor_id: int) -> MemberOut:
        member = await self._get_or_404(fund_id, member_id, for_update=True)
        self._ensure_not_self_or_chairman(member, actor_id)
        if member.status != ACTIVE:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member is not active")

        self._audit(member, "member.role", actor_id, role_from=member.role, role_to=role.value)
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

        # Сначала снимаем старого председателя: в БД уникальный индекс «один председатель на фонд»
        current.role = FundRoleEnum.admin.value
        await self.db.flush()
        target.role = FundRoleEnum.chairman.value
        self._audit(target, "member.chairman", current.user_id, previous_chairman_user_id=current.user_id)
        await self.db.commit()
        return member_out(target)

    # ─── Helpers ───────────────────────────────────────────────────────────────

    async def _balances_for(self, fund: Fund, members: list[FundMember]) -> dict[int, ResidentBalanceOut]:
        user_ids = [m.user_id for m in members]
        sums = await self.contribution_repo.monthly_sums_by_user(
            fund.id, currency=fund.base_currency, user_ids=user_ids
        )
        schedule = await self.rate_repo.schedule(fund.id)
        excluded = await self.pause_repo.excluded_periods(fund.id, [m.id for m in members])
        today = current_period()
        result = {}
        for member in members:
            # Начисления идут с месяца вступления, но не раньше старта фонда
            joined = period_of(member.joined_at) if member.joined_at else fund.start_period
            # Пока участник отсутствует (вышел / заблокирован), сальдо замирает на месяце ухода:
            # дальше начислять или нет — решит совет при возвращении
            since = away_since(member) if member.status != ACTIVE else None
            result[member.user_id] = calculate_balance(
                paid=sums.get(member.user_id, {}).get(APPROVED, 0),
                pending=sums.get(member.user_id, {}).get(PENDING, 0),
                schedule=schedule,
                start_period=max(fund.start_period, joined),
                today_period=period_of(since) if since else today,
                currency=fund.base_currency,
                excluded=excluded.get(member.id, set()),
            )
        return result

    @staticmethod
    def _absence(
        fund: Fund,
        member: FundMember,
        schedule: RateSchedule,
        balance: ResidentBalanceOut | None,
    ) -> AbsenceOut | None:
        """Предпросмотр решения для совета: возвращение после выхода или разблокировка."""
        returning = member.status == MemberStatusEnum.pending.value and member.left_at is not None
        unblocking = member.status == BLOCKED and member.left_at is None and member.blocked_at is not None
        since = away_since(member)
        if not (returning or unblocking) or since is None:
            return None

        periods = absence_periods(since, current_period())
        return AbsenceOut(
            reason="left" if returning else "blocked",
            since=since,
            from_period=periods[0] if periods else None,
            to_period=periods[-1] if periods else None,
            months_count=len(periods),
            amount=sum(rate_at(schedule, p) for p in periods),
            currency=fund.base_currency,
            debt_before=balance.debt_amount if balance else 0,
        )

    async def _decide_absence(
        self,
        member: FundMember,
        since: datetime,
        accrue: bool,
        reason: str,
        actor_id: int,
    ) -> None:
        """«Без начисления» — пауза на месяцы отсутствия; «с начислением» — ничего не меняем."""
        periods = absence_periods(since, current_period())
        if accrue or not periods:
            return
        await self.pause_repo.create(
            fund_id=member.fund_id,
            member_id=member.id,
            from_period=periods[0],
            to_period=periods[-1],
            reason=reason,
            decided_by_id=actor_id,
        )

    def _audit(self, member: FundMember, action: str, actor_id: int, **details) -> None:
        self.audit.add(
            fund_id=member.fund_id,
            actor_id=actor_id,
            action=action,
            entity="member",
            entity_id=member.id,
            details={"user_id": member.user_id, **details},
        )

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

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.enums import CurrencyEnum, FundRoleEnum, MemberStatusEnum
from app.schemas.balance import ResidentBalanceOut


class FundContext(BaseModel):
    """Активное членство текущего пользователя в фонде из URL (результат deps.fund)."""

    fund_id: int
    user_id: int
    member_id: int
    role: FundRoleEnum

    @property
    def is_council(self) -> bool:
        return self.role in (FundRoleEnum.admin, FundRoleEnum.chairman)

    @property
    def is_chairman(self) -> bool:
        return self.role == FundRoleEnum.chairman

    def can_see_receipt(self, owner_id: int) -> bool:
        """Чек — личный документ (номер карты, банк): видят владелец и совет."""
        return self.is_council or owner_id == self.user_id


class JoinIn(BaseModel):
    address_unit: str = Field(min_length=1, max_length=50)
    message: str | None = Field(None, max_length=500)


class MemberOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    phone: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    role: FundRoleEnum
    status: MemberStatusEnum
    address_unit: str | None = None
    message: str | None = None
    joined_at: datetime | None = None
    left_at: datetime | None = None
    blocked_at: datetime | None = None
    created_at: datetime


class AbsenceOut(BaseModel):
    """
    Период отсутствия, за который совет решает: начислять или нет.

    Месяц ухода и месяц возвращения начисляются всегда — решение касается только
    месяцев между ними. Долг до ухода сохраняется в любом случае.
    """

    reason: Literal["left", "blocked"]
    since: datetime  # дата выхода или блокировки
    from_period: str | None = None  # первый месяц отсутствия (None — решать не о чем)
    to_period: str | None = None
    months_count: int
    amount: int  # сколько начислится при выборе «с начислением»
    currency: CurrencyEnum
    debt_before: int  # долг на момент ухода — остаётся обязательно


class MemberOutCouncil(MemberOut):
    # Сальдо: у активных — на сегодня, у заблокированных и вышедших — на момент ухода
    balance: ResidentBalanceOut | None = None
    # Возвращающийся участник (заявка) или заблокированный — нужен выбор совета
    absence: AbsenceOut | None = None


class MemberApproveIn(BaseModel):
    # Обязательно для возвращающегося участника: начислять ли за период отсутствия
    accrue_absence: bool | None = None


class MemberStatusUpdateIn(BaseModel):
    status: Literal[MemberStatusEnum.active, MemberStatusEnum.blocked]
    # Обязательно при разблокировке: начислять ли за время блокировки
    accrue_absence: bool | None = None


class MemberRoleUpdateIn(BaseModel):
    role: Literal[FundRoleEnum.resident, FundRoleEnum.admin]


class ChairmanTransferIn(BaseModel):
    member_id: int

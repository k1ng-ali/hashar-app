from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.enums import ContributionStatusEnum, CurrencyEnum, FundRoleEnum, MemberStatusEnum, PlanEnum

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


# ─── Создание / настройки ─────────────────────────────────────────────────────


class FundCreateIn(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    description: str | None = Field(None, max_length=2000)
    address: str | None = Field(None, max_length=255)
    base_currency: CurrencyEnum = CurrencyEnum.tjs
    currencies: list[CurrencyEnum] = Field(default_factory=list)  # дополнительные счета, базовый добавится сам
    monthly_rate: int = Field(0, ge=0, le=10_000_000)
    start_period: str | None = Field(None, pattern=PERIOD_PATTERN)  # по умолчанию — текущий месяц
    address_unit: str | None = Field(None, max_length=50)  # помещение председателя


class FundUpdateIn(BaseModel):
    name: str | None = Field(None, min_length=3, max_length=150)
    description: str | None = Field(None, max_length=2000)
    address: str | None = Field(None, max_length=255)
    base_currency: CurrencyEnum | None = None
    # Новый тариф вступает в силу с 1-го числа следующего месяца
    monthly_rate: int | None = Field(None, ge=0, le=10_000_000)
    start_period: str | None = Field(None, pattern=PERIOD_PATTERN)


# ─── Ответы ───────────────────────────────────────────────────────────────────


class AccountOut(BaseModel):
    currency: CurrencyEnum
    is_active: bool
    balance: int


class RateOut(BaseModel):
    period: str  # действует с этого месяца
    amount: int


class PlanInfoOut(BaseModel):
    plan: PlanEnum  # купленный
    effective_plan: PlanEnum  # действующий (после истечения — free)
    expires_at: datetime | None = None
    member_limit: int | None = None  # None — без ограничений
    members_count: int
    price_tjs: int | None = None  # цена текущего тарифа за месяц
    # Стоимость неиспользованного остатка — при смене тарифа перейдёт в дни нового
    remaining_tjs: float | None = None


class FundOut(BaseModel):
    """Карточка фонда для его участников."""

    id: int
    name: str
    description: str | None = None
    address: str | None = None
    code: str
    base_currency: CurrencyEnum
    monthly_rate: int  # тариф текущего месяца
    next_monthly_rate: int | None = None  # запланированный тариф, если меняется
    next_rate_period: str | None = None  # с какого месяца
    rate_history: list[RateOut]
    start_period: str
    # Валюта и начало расчётов заблокированы: уже есть ежемесячные взносы
    setup_locked: bool = False
    accounts: list[AccountOut]
    plan: PlanInfoOut
    my_role: FundRoleEnum
    created_at: datetime


class FundPublicOut(BaseModel):
    """Результат поиска / превью по ссылке — без финансов."""

    id: int
    name: str
    address: str | None = None
    code: str
    members_count: int
    my_status: MemberStatusEnum | None = None


class MyFundOut(BaseModel):
    """Фонд в списке «мои фонды» вместе с моим членством."""

    id: int
    name: str
    address: str | None = None
    code: str
    base_currency: CurrencyEnum
    role: FundRoleEnum
    status: MemberStatusEnum
    address_unit: str | None = None


# ─── Главный экран ────────────────────────────────────────────────────────────


class AccountSummaryOut(BaseModel):
    currency: CurrencyEnum
    balance: int
    month_collected: int
    month_spent: int


class FundSummaryOut(BaseModel):
    base_currency: CurrencyEnum
    rate: int
    current_period: str
    accounts: list[AccountSummaryOut]
    pending_count: int  # чеки на проверке
    pending_members_count: int  # заявки на вступление
    active_members_count: int
    debtors_count: int


class OperationOut(BaseModel):
    """Единая лента операций: поступления, расходы и переводы между счетами."""

    id: str  # "c-<id>" / "e-<id>" / "t-<id>"
    type: Literal["income", "expense", "transfer"]
    category: str
    title: str
    subtitle: str
    amount: int
    currency: CurrencyEnum
    # Для перевода между счетами — списанная сторона (from)
    counter_amount: int | None = None
    counter_currency: CurrencyEnum | None = None
    status: ContributionStatusEnum | None = None
    receipt_image: str | None = None
    created_at: datetime

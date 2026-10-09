from pydantic import BaseModel

from app.enums import BalanceStatusEnum, CurrencyEnum


class ResidentBalanceOut(BaseModel):
    """Сальдо участника по ежемесячным взносам (в базовой валюте фонда)."""

    status: BalanceStatusEnum
    currency: CurrencyEnum
    rate: int
    balance: int  # оплачено - начислено (< 0 — долг, > 0 — аванс)
    total_due: int
    total_paid: int
    pending_amount: int  # чеки на проверке, в сальдо не входят
    has_pending: bool
    paid_months_count: int
    paid_until_period: str | None = None
    debt_amount: int
    debt_months_count: int
    advance_amount: int
    advance_months_count: int
    covered_periods: list[str]
    unpaid_periods: list[str]
    current_period: str
    next_billing_period: str

from backend.app.schemas.base import BaseSchema


class FundSummaryResponse(BaseSchema):
    total_balance: int
    total_collected: int
    total_expenses: int
    current_month_collected: int
    current_month_spent: int
    pending_contributions_count: int
    pending_contributions_amount: int
    active_residents_count: int
    debtors_count: int


class ResidentBalanceStatusResponse(BaseSchema):
    paid_months_count: int
    paid_until_period: str | None
    debt_months_count: int
    debt_amount: int
    advance_months_count: int
    advance_amount: int
    status_type: str  # OK, DEBT, ADVANCE
    balance: int
    total_paid: int
    total_due: int
    has_pending: bool
    pending_amount: int
    next_billing_period: str
    next_billing_date: str
    next_billing_amount: int
    covered_periods: list[str]
    unpaid_periods: list[str]

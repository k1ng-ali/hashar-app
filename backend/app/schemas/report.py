from pydantic import BaseModel

from app.enums import CurrencyEnum, ExpenseCategoryEnum


class MonthlyLedgerRowOut(BaseModel):
    period: str  # YYYY-MM
    income: int
    expense: int
    delta: int
    is_current: bool


class CategoryStatOut(BaseModel):
    category: ExpenseCategoryEnum
    total: int
    percent: int


class FinancialReportOut(BaseModel):
    currency: CurrencyEnum
    currencies: list[CurrencyEnum]  # включённые счета — для переключателя
    base_currency: CurrencyEnum
    monthly_rows: list[MonthlyLedgerRowOut]
    category_stats: list[CategoryStatOut]
    total_income: int
    total_expense: int
    net_balance: int
    rate: int


class DebtorOut(BaseModel):
    member_id: int
    user_id: int
    full_name: str
    address_unit: str | None = None
    phone: str | None = None
    debt_amount: int
    currency: CurrencyEnum
    debt_months_count: int
    unpaid_periods: list[str]

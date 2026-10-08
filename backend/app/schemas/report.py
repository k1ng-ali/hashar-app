from backend.app.schemas.base import BaseSchema


class MonthlyLedgerRow(BaseSchema):
    period: str
    title: str
    income: int
    expense: int
    delta: int
    is_current: bool


class CategoryStat(BaseSchema):
    name: str
    total: int
    percent: int


class FinancialReportResponse(BaseSchema):
    monthly_rows: list[MonthlyLedgerRow]
    category_stats: list[CategoryStat]
    total_income: int
    total_expense: int
    net_balance: int

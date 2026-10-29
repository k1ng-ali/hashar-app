import csv
import io
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.finance import current_period, rate_at, shift_period
from app.core.formatting import display_phone
from app.enums import CurrencyEnum
from app.repositories.contribution_repo import ContributionRepository
from app.repositories.expense_repo import ExpenseRepository
from app.repositories.fund_rate_repo import FundRateRepository
from app.repositories.fund_repo import FundRepository
from app.repositories.transfer_repo import TransferRepository
from app.schemas.report import CategoryStatOut, DebtorOut, FinancialReportOut, MonthlyLedgerRowOut
from app.services.account_service import AccountService
from app.services.member_service import MemberService

# Лимит строк в CSV-выгрузке
EXPORT_LIMIT = 10_000

STATUS_TITLES = {"pending": "На проверке", "approved": "Одобрено", "rejected": "Отклонено"}
CATEGORY_TITLES = {"monthly_fee": "Ежемесячный взнос", "target_fund": "Целевой сбор"}


class ReportService:
    """
    Финансовая отчётность фонда и CSV-выгрузки (UTF-8 BOM, разделитель `;` — для Excel).
    Первая колонка не должна называться «ID»: такой файл Excel принимает за формат SYLK и открывает пустым.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fund_repo = FundRepository(db=db)
        self.rate_repo = FundRateRepository(db=db)
        self.contribution_repo = ContributionRepository(db=db)
        self.expense_repo = ExpenseRepository(db=db)
        self.transfer_repo = TransferRepository(db=db)
        self.accounts = AccountService(db=db)
        self.members = MemberService(db=db)

    async def financial(
        self, fund_id: int, currency: CurrencyEnum | None = None, months: int = 6
    ) -> FinancialReportOut:
        fund = await self.fund_repo.get(fund_id)
        currencies = await self.accounts.active_currencies(fund_id)
        code = currency.value if currency else fund.base_currency
        if code not in currencies:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Currency account is not enabled")

        income_by_month = await self.contribution_repo.approved_monthly_sums(fund_id, currency=code)
        expense_by_month = await self.expense_repo.monthly_sums(fund_id, currency=code)
        today = current_period()

        rows = []
        for i in range(months):
            period = shift_period(today, -i)
            income = income_by_month.get(period, 0)
            expense = expense_by_month.get(period, 0)
            rows.append(
                MonthlyLedgerRowOut(
                    period=period,
                    income=income,
                    expense=expense,
                    delta=income - expense,
                    is_current=period == today,
                )
            )

        by_category = await self.expense_repo.sums_by_category(fund_id, currency=code)
        total_expense = sum(by_category.values())
        category_stats = sorted(
            (
                CategoryStatOut(category=category, total=total, percent=round(total / (total_expense or 1) * 100))
                for category, total in by_category.items()
                if total > 0
            ),
            key=lambda stat: stat.total,
            reverse=True,
        )

        total_income = sum(income_by_month.values())
        return FinancialReportOut(
            currency=code,
            currencies=currencies,
            base_currency=fund.base_currency,
            monthly_rows=rows,
            category_stats=category_stats,
            total_income=total_income,
            total_expense=total_expense,
            # Остаток счёта учитывает и переводы между валютами
            net_balance=(await self.accounts.balances(fund_id))[code],
            rate=rate_at(await self.rate_repo.schedule(fund_id), current_period()),
        )

    async def debtors(self, fund_id: int) -> list[DebtorOut]:
        return await self.members.list_debtors(fund_id)

    # ─── CSV ───────────────────────────────────────────────────────────────────

    async def export_contributions(self, fund_id: int) -> tuple[str, str]:
        items = await self.contribution_repo.list(fund_id, limit=EXPORT_LIMIT)
        rows = [
            [
                c.id,
                c.created_at.strftime("%Y-%m-%d %H:%M"),
                c.user.full_name,
                c.user_unit or "",
                CATEGORY_TITLES.get(c.category, c.category),
                c.billing_period or (c.target_fund.title if c.target_fund else ""),
                c.amount,
                c.currency.upper(),
                c.credited_amount,
                c.credited_currency.upper(),
                c.requisite_label or "",
                STATUS_TITLES.get(c.status, c.status),
                c.reviewed_by.full_name if c.reviewed_by else "",
                c.comment_admin or c.comment_user or "",
            ]
            for c in items
        ]
        header = [
            "№", "Дата", "Участник", "Помещение", "Категория", "Период / Сбор",
            "Сумма", "Валюта", "Зачтено", "Валюта зачёта", "Реквизит", "Статус", "Проверил", "Комментарий",
        ]  # fmt: skip
        return self._filename("reestr_vznosov"), self._to_csv(header, rows)

    async def export_expenses(self, fund_id: int) -> tuple[str, str]:
        items = await self.expense_repo.list(fund_id, limit=EXPORT_LIMIT)
        rows = [
            [
                e.id,
                e.created_at.strftime("%Y-%m-%d %H:%M"),
                e.title,
                e.category,
                e.amount,
                e.currency.upper(),
                e.target_fund.title if e.target_fund else "",
                e.created_by.full_name if e.created_by else "",
                e.description,
            ]
            for e in items
        ]
        header = ["№", "Дата", "Название", "Категория", "Сумма", "Валюта", "Целевой сбор", "Ответственный", "Описание"]
        return self._filename("reestr_rashodov"), self._to_csv(header, rows)

    async def export_debtors(self, fund_id: int) -> tuple[str, str]:
        debtors = await self.members.list_debtors(fund_id)
        rows = [
            [
                d.address_unit or "",
                d.full_name,
                display_phone(d.phone),
                d.debt_amount,
                d.currency.upper(),
                d.debt_months_count,
                ", ".join(d.unpaid_periods),
            ]
            for d in debtors
        ]
        header = ["Помещение", "Участник", "Телефон", "Сумма долга", "Валюта", "Месяцев", "Неоплаченные периоды"]
        return self._filename("reestr_dolzhnikov"), self._to_csv(header, rows)

    @staticmethod
    def _to_csv(header: list[str], rows: list[list]) -> str:
        output = io.StringIO()
        output.write("﻿")
        writer = csv.writer(output, delimiter=";")
        writer.writerow(header)
        writer.writerows(rows)
        return output.getvalue()

    @staticmethod
    def _filename(prefix: str) -> str:
        return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.csv"

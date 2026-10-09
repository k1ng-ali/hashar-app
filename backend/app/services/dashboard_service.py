from datetime import datetime
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.finance import current_period, shift_period
from app.enums import ContributionCategoryEnum
from app.repositories.contribution_repo import ContributionRepository
from app.repositories.expense_repo import ExpenseRepository
from app.repositories.fund_repo import FundRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.transfer_repo import TransferRepository
from app.schemas.fund import AccountSummaryOut, FundSummaryOut, OperationOut
from app.services.account_service import AccountService
from app.services.member_service import MemberService

OperationsFilter = Literal["all", "income", "expense", "transfer"]


def period_bounds(period: str) -> tuple[datetime, datetime]:
    """Границы месяца [начало, начало следующего) в UTC."""
    start = datetime.fromisoformat(f"{period}-01T00:00:00+00:00")
    end = datetime.fromisoformat(f"{shift_period(period, 1)}-01T00:00:00+00:00")
    return start, end


class DashboardService:
    """Главный экран фонда: остатки по валютам и лента операций."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fund_repo = FundRepository(db=db)
        self.contribution_repo = ContributionRepository(db=db)
        self.expense_repo = ExpenseRepository(db=db)
        self.transfer_repo = TransferRepository(db=db)
        self.member_repo = MemberRepository(db=db)
        self.accounts = AccountService(db=db)
        self.members = MemberService(db=db)

    async def summary(self, fund_id: int) -> FundSummaryOut:
        fund = await self.fund_repo.get(fund_id)
        today = current_period()
        start, end = period_bounds(today)

        balances = await self.accounts.balances(fund_id)
        collected = await self.contribution_repo.approved_sums_by_currency(fund_id, start=start, end=end)
        spent = await self.expense_repo.sums_by_currency(fund_id, start=start, end=end)

        return FundSummaryOut(
            base_currency=fund.base_currency,
            rate=fund.monthly_rate,
            current_period=today,
            accounts=[
                AccountSummaryOut(
                    currency=currency,
                    balance=balances[currency],
                    month_collected=collected.get(currency, 0),
                    month_spent=spent.get(currency, 0),
                )
                for currency in await self.accounts.active_currencies(fund_id)
            ],
            pending_count=await self.contribution_repo.count_pending(fund_id),
            active_members_count=await self.member_repo.count_active(fund_id),
            debtors_count=len(await self.members.list_debtors(fund_id)),
        )

    async def operations(
        self,
        fund_id: int,
        type_filter: OperationsFilter = "all",
        limit: int = 10,
    ) -> list[OperationOut]:
        operations: list[OperationOut] = []

        if type_filter in ("all", "income"):
            for c in await self.contribution_repo.list(fund_id, limit=limit):
                is_target = c.category == ContributionCategoryEnum.target_fund.value and c.target_fund
                operations.append(
                    OperationOut(
                        id=f"c-{c.id}",
                        type="income",
                        category=c.category,
                        title=f"{c.user.full_name} ({c.user_unit})" if c.user_unit else c.user.full_name,
                        # Пустая подпись — фронт подставит «Ежемесячный взнос» из i18n
                        subtitle=c.target_fund.title if is_target else "",
                        amount=c.amount,
                        currency=c.currency,
                        status=c.status,
                        receipt_image=c.receipt_image,
                        created_at=c.created_at,
                    )
                )

        if type_filter in ("all", "expense"):
            for e in await self.expense_repo.list(fund_id, limit=limit):
                operations.append(
                    OperationOut(
                        id=f"e-{e.id}",
                        type="expense",
                        category=e.category,
                        title=e.title,
                        subtitle=e.created_by.full_name if e.created_by else "",
                        amount=e.amount,
                        currency=e.currency,
                        receipt_image=e.receipt_images[0] if e.receipt_images else None,
                        created_at=e.created_at,
                    )
                )

        if type_filter in ("all", "transfer"):
            for t in await self.transfer_repo.list(fund_id, limit=limit):
                # В ленте показываем сторону зачисления (или списания для корректировки)
                operations.append(
                    OperationOut(
                        id=f"t-{t.id}",
                        type="transfer",
                        category="transfer" if t.from_currency and t.to_currency else "correction",
                        title=t.comment,
                        subtitle=t.created_by.full_name if t.created_by else "",
                        amount=t.to_amount if t.to_amount is not None else -t.from_amount,
                        currency=t.to_currency or t.from_currency,
                        counter_amount=t.from_amount if t.to_currency else None,
                        counter_currency=t.from_currency if t.to_currency else None,
                        created_at=t.created_at,
                    )
                )

        operations.sort(key=lambda op: op.created_at, reverse=True)
        return operations[:limit]

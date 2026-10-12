from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import CurrencyEnum, ExpenseCategoryEnum
from app.models.expense import Expense
from app.repositories.expense_repo import ExpenseRepository
from app.repositories.target_fund_repo import TargetFundRepository
from app.schemas.expense import ExpenseCreateIn, ExpenseOut
from app.services.account_service import AccountService


def expense_out(expense: Expense) -> ExpenseOut:
    return ExpenseOut(
        id=expense.id,
        title=expense.title,
        category=expense.category,
        amount=expense.amount,
        currency=expense.currency,
        description=expense.description,
        receipt_images=list(expense.receipt_images or []),
        target_fund_id=expense.target_fund_id,
        target_fund_title=expense.target_fund.title if expense.target_fund else None,
        created_by_name=expense.created_by.full_name if expense.created_by else None,
        created_at=expense.created_at,
    )


class ExpenseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ExpenseRepository(db=db)
        self.target_fund_repo = TargetFundRepository(db=db)
        self.accounts = AccountService(db=db)

    async def list(
        self,
        fund_id: int,
        category: ExpenseCategoryEnum | None = None,
        currency: CurrencyEnum | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ExpenseOut]:
        items = await self.repo.list(
            fund_id,
            category=category.value if category else None,
            currency=currency.value if currency else None,
            skip=skip,
            limit=limit,
        )
        return [expense_out(item) for item in items]

    async def get(self, fund_id: int, expense_id: int) -> ExpenseOut:
        expense = await self.repo.get(fund_id, expense_id)
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
        return expense_out(expense)

    async def create(self, fund_id: int, user_id: int, payload: ExpenseCreateIn) -> ExpenseOut:
        await self.accounts.ensure_active_currency(fund_id, payload.currency.value)

        if payload.target_fund_id is not None:
            target_fund = await self.target_fund_repo.get(fund_id, payload.target_fund_id)
            if not target_fund:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target fund not found")
            if target_fund.currency != payload.currency.value:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Currency must match the target fund")

        await self.accounts.ensure_sufficient(fund_id, payload.currency.value, payload.amount, payload.allow_overdraft)

        expense = await self.repo.create(
            fund_id=fund_id,
            title=payload.title,
            category=payload.category.value,
            amount=payload.amount,
            currency=payload.currency.value,
            description=payload.description,
            receipt_images=payload.receipt_images,
            target_fund_id=payload.target_fund_id,
            created_by_id=user_id,
        )
        await self.db.commit()
        return expense_out(expense)

    async def delete(self, fund_id: int, expense_id: int) -> None:
        expense = await self.repo.get(fund_id, expense_id)
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
        await self.repo.delete(expense)
        await self.db.commit()

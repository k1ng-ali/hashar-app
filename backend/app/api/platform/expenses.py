from fastapi import APIRouter, Depends, Query

from app.deps.fund import get_fund_context
from app.deps.services import get_expense_service
from app.enums import CurrencyEnum, ExpenseCategoryEnum
from app.schemas.expense import ExpenseOut
from app.schemas.member import FundContext
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/funds/{fund_id}/expenses", tags=["Platform • Expenses"])


@router.get("/", response_model=list[ExpenseOut])
async def list_expenses(
    category: ExpenseCategoryEnum | None = None,
    currency: CurrencyEnum | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    ctx: FundContext = Depends(get_fund_context),
    service: ExpenseService = Depends(get_expense_service),
):
    return await service.list(fund_id=ctx.fund_id, category=category, currency=currency, skip=skip, limit=limit)


@router.get("/{expense_id}", response_model=ExpenseOut)
async def get_expense(
    expense_id: int,
    ctx: FundContext = Depends(get_fund_context),
    service: ExpenseService = Depends(get_expense_service),
):
    return await service.get(fund_id=ctx.fund_id, expense_id=expense_id)

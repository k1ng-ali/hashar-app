from fastapi import APIRouter, Depends, status

from app.deps.fund import require_fund_chairman, require_fund_council
from app.deps.services import get_expense_service
from app.schemas.expense import ExpenseCreateIn, ExpenseOut
from app.schemas.member import FundContext
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/funds/{fund_id}/expenses", tags=["Council • Expenses"])


@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreateIn,
    ctx: FundContext = Depends(require_fund_council),
    service: ExpenseService = Depends(get_expense_service),
):
    return await service.create(fund_id=ctx.fund_id, user_id=ctx.user_id, payload=payload)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    ctx: FundContext = Depends(require_fund_chairman),
    service: ExpenseService = Depends(get_expense_service),
):
    await service.delete(fund_id=ctx.fund_id, expense_id=expense_id, user_id=ctx.user_id)

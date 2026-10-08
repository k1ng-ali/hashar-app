import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.expense import Expense
from backend.app.models.user import User
from backend.app.schemas.expense import ExpenseResponse, ExpenseCreate
from backend.app.api.deps import get_current_admin

router = APIRouter()


@router.get("/", response_model=list[ExpenseResponse])
def get_expenses(db: Session = Depends(get_db)):
    return db.query(Expense).order_by(Expense.created_at.desc()).all()


@router.post("/", response_model=ExpenseResponse)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    expense_id = f"exp_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"
    expense = Expense(
        id=expense_id,
        title=payload.title,
        category=payload.category,
        amount=payload.amount,
        description=payload.description,
        receipt_image_paths=payload.receipt_image_paths,
        target_fund_id=payload.target_fund_id,
        target_fund_title=payload.target_fund_title,
        created_by_admin_id=admin.id,
        created_by_admin_name=admin.full_name,
        created_at=datetime.now(timezone.utc),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Расход не найден")
    db.delete(expense)
    db.commit()
    return None

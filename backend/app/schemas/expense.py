from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import CurrencyEnum, ExpenseCategoryEnum
from app.schemas.contribution import ReceiptImage

MAX_EXPENSE_IMAGES = 3


class ExpenseCreateIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    category: ExpenseCategoryEnum
    amount: int = Field(ge=1, le=100_000_000)
    currency: CurrencyEnum  # счёт фонда, с которого списываем
    description: str = Field(min_length=3, max_length=5000)
    # Чек, фото проблемы, фото результата — до трёх
    receipt_images: list[ReceiptImage] = Field(default_factory=list, max_length=MAX_EXPENSE_IMAGES)
    target_fund_id: int | None = None
    # Расход больше остатка счёта проводится только с явным подтверждением
    allow_overdraft: bool = False


class ExpenseOut(BaseModel):
    id: int
    title: str
    category: ExpenseCategoryEnum
    amount: int
    currency: CurrencyEnum
    description: str
    receipt_images: list[str]
    target_fund_id: int | None = None
    target_fund_title: str | None = None
    created_by_name: str | None = None
    created_at: datetime

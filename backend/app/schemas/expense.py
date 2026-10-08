from datetime import datetime
from pydantic import Field
from backend.app.schemas.base import BaseSchema


class ExpenseBase(BaseSchema):
    title: str = Field(..., min_length=3, max_length=200, example="Замена прожекторов освещения во дворе")
    category: str = Field(..., example="Электрика")
    amount: int = Field(..., ge=100, example=14200)
    description: str = Field(..., example="Куплены светодиодные уличные прожекторы Jazzway 50W...")
    receipt_image_paths: list[str] = Field(default_factory=list)
    target_fund_id: int | None = None
    target_fund_title: str | None = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseResponse(ExpenseBase):
    id: str
    created_by_admin_id: str
    created_by_admin_name: str
    created_at: datetime

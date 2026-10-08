from datetime import datetime
from pydantic import Field
from backend.app.schemas.base import BaseSchema


class TargetFundBase(BaseSchema):
    title: str = Field(..., min_length=3, max_length=200, example="Автоматический шлагбаум и видеонаблюдение въезда")
    description: str = Field(..., example="Установка GSM-модуля, стрелы шлагбаума и 2 камер...")
    target_amount: int = Field(..., ge=1000, example=280000)
    category: str = Field("Благоустройство", example="Безопасность")
    is_active: bool = True


class TargetFundCreate(TargetFundBase):
    pass


class TargetFundUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    target_amount: int | None = None
    category: str | None = None
    is_active: bool | None = None


class TargetFundResponse(TargetFundBase):
    id: int
    collected_amount: int = 0
    created_by_admin_id: str | None = None
    created_at: datetime

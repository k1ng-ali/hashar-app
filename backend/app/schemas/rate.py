from datetime import datetime
from pydantic import Field
from backend.app.schemas.base import BaseSchema


class BillingRateBase(BaseSchema):
    amount: int = Field(..., ge=100, example=1500)
    effective_from: str = Field(..., example="2026-01-01")


class BillingRateCreate(BillingRateBase):
    pass


class BillingRateResponse(BillingRateBase):
    id: int
    created_by_admin_id: str | None = None
    created_at: datetime

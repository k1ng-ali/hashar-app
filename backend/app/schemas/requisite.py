from pydantic import Field
from backend.app.schemas.base import BaseSchema


class PaymentRequisiteBase(BaseSchema):
    bank_name: str = Field(..., example="Сбербанк")
    card_or_account_number: str = Field(..., example="2202 2034 5678 9101")
    recipient_name: str = Field(..., example="Алексей Викторович Н. (Председатель)")
    phone_number: str | None = Field(None, example="+7 (916) 123-45-67")
    is_active: bool = True
    note: str | None = None


class PaymentRequisiteCreate(PaymentRequisiteBase):
    pass


class PaymentRequisiteResponse(PaymentRequisiteBase):
    id: int

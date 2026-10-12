from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.formatting import format_account, format_card, format_phone
from app.enums import CurrencyEnum

# ─── Счета ────────────────────────────────────────────────────────────────────


class AccountCreateIn(BaseModel):
    currency: CurrencyEnum


# ─── Реквизиты ────────────────────────────────────────────────────────────────


class RequisiteCreateIn(BaseModel):
    currency: CurrencyEnum
    kind: Literal["card", "account"] = "card"
    bank_name: str = Field(min_length=2, max_length=100)
    card_or_account_number: str = Field(min_length=4, max_length=50)
    recipient_name: str = Field(min_length=2, max_length=120)
    phone_number: str | None = Field(None, max_length=30)
    note: str | None = Field(None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self):
        # Номер и телефон — проверка и единый формат (как во фронтенде)
        number = self.card_or_account_number
        self.card_or_account_number = format_card(number) if self.kind == "card" else format_account(number)
        if self.phone_number is not None and self.phone_number.strip():
            self.phone_number = format_phone(self.phone_number)
        else:
            self.phone_number = None
        return self


class RequisiteOut(BaseModel):
    id: int
    currency: CurrencyEnum
    kind: Literal["card", "account"]
    bank_name: str
    card_or_account_number: str
    recipient_name: str
    phone_number: str | None = None
    note: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ─── Переводы и корректировки ─────────────────────────────────────────────────


class TransferCreateIn(BaseModel):
    """
    Перевод: заполнены обе стороны (from и to).
    Корректировка: заполнена только одна сторона — списание (from) или зачисление (to).
    """

    from_currency: CurrencyEnum | None = None
    from_amount: int | None = Field(None, ge=1, le=100_000_000)
    to_currency: CurrencyEnum | None = None
    to_amount: int | None = Field(None, ge=1, le=100_000_000)
    comment: str = Field(min_length=3, max_length=1000)
    # Списание больше остатка счёта проводится только с явным подтверждением
    allow_overdraft: bool = False

    @model_validator(mode="after")
    def check_sides(self):
        if (self.from_currency is None) != (self.from_amount is None):
            raise ValueError("from_currency and from_amount must be set together")
        if (self.to_currency is None) != (self.to_amount is None):
            raise ValueError("to_currency and to_amount must be set together")
        if self.from_currency is None and self.to_currency is None:
            raise ValueError("at least one side is required")
        if self.from_currency is not None and self.from_currency == self.to_currency:
            raise ValueError("currencies must differ")
        return self


class TransferOut(BaseModel):
    id: int
    from_currency: CurrencyEnum | None = None
    from_amount: int | None = None
    to_currency: CurrencyEnum | None = None
    to_amount: int | None = None
    comment: str
    created_by_name: str | None = None
    created_at: datetime

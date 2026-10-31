import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums import DiscountKindEnum, DiscountStateEnum, PlanEnum, PromoStatusEnum

# Скидки и прайс есть только у тарифов с ценой из каталога
PricedPlan = Literal[PlanEnum.pro, PlanEnum.max]

PROMO_CODE = re.compile(r"[A-Z0-9_-]{3,30}")


def normalize_code(code: str) -> str:
    return code.strip().upper()


# ─── Витрина ──────────────────────────────────────────────────────────────────


class PlanSaleOut(BaseModel):
    """Распродажа на витрине тарифов."""

    title: str
    kind: DiscountKindEnum
    value: int
    ends_at: datetime | None = None


class PlanOptionOut(BaseModel):
    """Строка каталога тарифов: price_tjs — к оплате, list_price_tjs — без скидки."""

    plan: PlanEnum
    member_limit: int | None = None
    price_tjs: int | None = None
    list_price_tjs: int | None = None
    sale: PlanSaleOut | None = None


class PlanQuoteOut(BaseModel):
    """Сколько заплатит фонд и что будет с остатком текущего тарифа."""

    plan: PlanEnum
    months: int
    list_price_tjs: int | None = None
    price_tjs: int | None = None
    total_tjs: int | None = None
    discount_label: str | None = None
    promo_status: PromoStatusEnum = PromoStatusEnum.none
    # True — тот же тариф по той же цене: срок добавится к дате окончания
    is_extension: bool = False
    carryover_tjs: float | None = None
    carryover_days: int | None = None


# ─── Админ платформы ──────────────────────────────────────────────────────────


class PlanPriceIn(BaseModel):
    price_tjs: int = Field(ge=1, le=1_000_000)


class PlanPriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan: PlanEnum
    price_tjs: int
    updated_at: datetime


class PlanDiscountIn(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    # Пусто — распродажа для всех, задан — промокод
    code: str | None = None
    kind: DiscountKindEnum
    value: int = Field(ge=1, le=1_000_000)
    plans: list[PricedPlan] = Field(min_length=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    max_uses: int | None = Field(None, ge=1)
    is_active: bool = True

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        return value.strip()

    @field_validator("code")
    @classmethod
    def check_code(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        code = normalize_code(value)
        if not PROMO_CODE.fullmatch(code):
            raise ValueError("Promo code must be 3-30 letters, digits, _ or -")
        return code

    @model_validator(mode="after")
    def check_rules(self) -> "PlanDiscountIn":
        if self.kind == DiscountKindEnum.percent and self.value > 99:
            raise ValueError("Percent discount must be 1-99")
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("Discount must end after it starts")
        if self.code is None and self.max_uses is not None:
            raise ValueError("Usage limit applies only to promo codes")
        return self


class PlanDiscountOut(BaseModel):
    id: int
    title: str
    code: str | None = None
    kind: DiscountKindEnum
    value: int
    plans: list[PlanEnum]
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    max_uses: int | None = None
    uses: int
    is_active: bool
    state: DiscountStateEnum
    created_at: datetime


class PricingOut(BaseModel):
    prices: list[PlanPriceOut]
    discounts: list[PlanDiscountOut]

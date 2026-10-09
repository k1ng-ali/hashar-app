from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import CurrencyEnum, TargetFundCategoryEnum
from app.schemas.contribution import ContributionOut


class TargetFundCreateIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3)
    target_amount: int = Field(ge=1, le=100_000_000)
    currency: CurrencyEnum
    category: TargetFundCategoryEnum = TargetFundCategoryEnum.landscaping


class TargetFundUpdateIn(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=3)
    target_amount: int | None = Field(None, ge=1, le=100_000_000)
    category: TargetFundCategoryEnum | None = None
    is_active: bool | None = None


class TargetFundOut(BaseModel):
    id: int
    title: str
    description: str
    target_amount: int
    currency: CurrencyEnum
    category: TargetFundCategoryEnum
    is_active: bool
    collected_amount: int
    remaining_amount: int
    percent: int
    contributors_count: int
    created_at: datetime


class MonthAmountOut(BaseModel):
    period: str  # YYYY-MM
    amount: int


class TargetFundDetailOut(TargetFundOut):
    average_contribution: int
    monthly: list[MonthAmountOut]
    contributions: list[ContributionOut]

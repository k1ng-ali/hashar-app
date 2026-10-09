from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.enums import ContributionCategoryEnum, ContributionStatusEnum, CurrencyEnum

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class ContributionCreateIn(BaseModel):
    # Реквизит, на который перевели деньги, — из него берётся валюта взноса
    requisite_id: int
    amount: int = Field(ge=1, le=10_000_000)
    category: ContributionCategoryEnum = ContributionCategoryEnum.monthly_fee
    target_fund_id: int | None = None
    billing_period: str | None = Field(None, pattern=PERIOD_PATTERN)
    receipt_image: str = Field(min_length=10)
    comment_user: str | None = Field(None, max_length=1000)

    @model_validator(mode="after")
    def check_target_fund(self):
        if self.category == ContributionCategoryEnum.target_fund and not self.target_fund_id:
            raise ValueError("target_fund_id is required for target_fund category")
        return self


class ContributionApproveIn(BaseModel):
    comment_admin: str | None = Field(None, max_length=1000)


class ContributionRejectIn(BaseModel):
    comment_admin: str = Field(min_length=3, max_length=1000)


class ContributionOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_unit: str | None = None
    amount: int
    currency: CurrencyEnum
    category: ContributionCategoryEnum
    target_fund_id: int | None = None
    target_fund_title: str | None = None
    billing_period: str | None = None
    receipt_image: str
    status: ContributionStatusEnum
    comment_user: str | None = None
    comment_admin: str | None = None
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

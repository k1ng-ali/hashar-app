from datetime import datetime
from pydantic import Field
from backend.app.schemas.base import BaseSchema
from backend.app.models.contribution import ContributionCategory, ContributionStatus


class ContributionBase(BaseSchema):
    amount: int = Field(..., ge=50, example=1500)
    category: ContributionCategory = ContributionCategory.MONTHLY_FEE
    target_fund_id: int | None = None
    billing_period: str | None = Field(None, example="2026-09")
    receipt_image_path: str = Field(..., example="data:image/svg+xml;utf8,...")
    comment_user: str | None = None


class ContributionCreate(ContributionBase):
    pass


class ContributionVerify(BaseSchema):
    status: ContributionStatus  # APPROVED or REJECTED
    comment_admin: str | None = None


class ContributionResponse(ContributionBase):
    id: str
    user_id: str
    user_name: str
    user_unit: str
    target_fund_title: str | None = None
    status: ContributionStatus
    comment_admin: str | None = None
    reviewed_by_admin_id: str | None = None
    reviewed_by_admin_name: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

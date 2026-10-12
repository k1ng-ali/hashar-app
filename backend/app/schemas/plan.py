from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.enums import FundRoleEnum, PlanEnum, PlanRequestStatusEnum


class PlanOptionOut(BaseModel):
    """Строка каталога тарифов."""

    plan: PlanEnum
    member_limit: int | None = None
    price_tjs: int | None = None


class PlanRequestIn(BaseModel):
    plan: Literal[PlanEnum.pro, PlanEnum.max, PlanEnum.individual]
    months: int = Field(1, ge=1, le=12)
    # Как связаться с председателем по оплате: телефон, Telegram, email
    contact: str = Field(min_length=3, max_length=150)
    comment: str | None = Field(None, max_length=1000)


class PlanRequestOut(BaseModel):
    id: int
    fund_id: int
    fund_name: str
    plan: PlanEnum
    months: int
    status: PlanRequestStatusEnum
    contact: str
    comment: str | None = None
    admin_comment: str | None = None
    requested_by_name: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime


# ─── Админ платформы ──────────────────────────────────────────────────────────


class PlanApproveIn(BaseModel):
    months: int | None = Field(None, ge=1, le=36)  # по умолчанию — из заявки
    member_limit: int | None = Field(None, ge=1)  # только для individual
    admin_comment: str | None = Field(None, max_length=1000)


class PlanRejectIn(BaseModel):
    admin_comment: str = Field(min_length=3, max_length=1000)


class FundPlanSetIn(BaseModel):
    """Ручная установка тарифа админом платформы."""

    plan: PlanEnum
    expires_at: datetime | None = None
    member_limit: int | None = Field(None, ge=1)


class FundCouncilMemberOut(BaseModel):
    """Председатель или администратор фонда с контактами — для админа платформы."""

    user_id: int
    full_name: str
    role: FundRoleEnum
    phone: str | None = None
    email: str | None = None
    address_unit: str | None = None


class FundOutAdmin(BaseModel):
    id: int
    name: str
    code: str
    address: str | None = None
    plan: PlanEnum
    effective_plan: PlanEnum
    plan_expires_at: datetime | None = None
    member_limit: int | None = None
    members_count: int
    council: list[FundCouncilMemberOut]
    created_at: datetime

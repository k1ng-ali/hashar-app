"""Аналитика платформы для админа: сводка, тарифы и выручка, здоровье фондов, пользователи, журнал."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.enums import FundRoleEnum, MemberStatusEnum, PlanEnum

# ─── Обзор ────────────────────────────────────────────────────────────────────


class PlatformTotalsOut(BaseModel):
    users_total: int  # без удалённых аккаунтов
    users_new_30d: int
    users_active_7d: int  # был вход/обновление токена за 7 дней
    users_active_30d: int
    funds_total: int
    funds_new_30d: int
    funds_active_30d: int  # был взнос или расход за 30 дней
    members_active: int
    pending_contributions: int  # чеки ждут совета
    pending_members: int  # заявки на вступление
    pending_plan_requests: int


class VerificationStatsOut(BaseModel):
    verified: int
    unverified: int
    google: int  # привязан вход через Google
    sms: int  # хотя бы раз подтвердили код из SMS


class GrowthPointOut(BaseModel):
    period: str  # YYYY-MM
    users: int  # новых за месяц
    funds: int
    users_total: int  # накопительно на конец месяца
    funds_total: int


class MoneyPointOut(BaseModel):
    period: str
    currency: str
    contributions: int  # одобренные взносы (в валюте оплаты)
    expenses: int  # расходы без отменённых


class CurrencyTotalOut(BaseModel):
    currency: str
    contributions: int
    expenses: int


class PlatformOverviewOut(BaseModel):
    totals: PlatformTotalsOut
    verification: VerificationStatsOut
    growth: list[GrowthPointOut]
    money: list[MoneyPointOut]
    currencies: list[CurrencyTotalOut]


# ─── Тарифы и выручка ─────────────────────────────────────────────────────────


class PlanShareOut(BaseModel):
    plan: PlanEnum
    funds: int


class RevenuePointOut(BaseModel):
    period: str
    amount_tjs: int
    approvals: int


class ExpiringFundOut(BaseModel):
    id: int
    name: str
    code: str
    plan: PlanEnum
    plan_expires_at: datetime


class PlanRequestStatsOut(BaseModel):
    pending: int
    approved: int
    rejected: int


class PlatformPlansOut(BaseModel):
    distribution: list[PlanShareOut]  # по действующему тарифу
    revenue: list[RevenuePointOut]
    revenue_total_tjs: int
    revenue_30d_tjs: int
    mrr_tjs: int  # сумма месячных цен действующих платных тарифов
    requests: PlanRequestStatsOut
    expiring: list[ExpiringFundOut]


# ─── Фонды ────────────────────────────────────────────────────────────────────

FundSort = Literal["created", "members", "activity", "pending"]


class FundHealthOut(BaseModel):
    id: int
    name: str
    code: str
    address: str | None = None
    effective_plan: PlanEnum
    plan_expires_at: datetime | None = None
    members_active: int
    member_limit: int | None = None
    pending_members: int
    pending_contributions: int
    stale_contributions: int  # чеки ждут дольше 3 дней
    contributions_30d: int
    last_activity_at: datetime | None = None  # последний взнос или расход
    inactive: bool  # ничего не было 30 дней
    created_at: datetime


class FundHealthListOut(BaseModel):
    items: list[FundHealthOut]
    total: int


# ─── Пользователи ─────────────────────────────────────────────────────────────


class UserOutAdmin(BaseModel):
    id: int
    full_name: str
    phone: str | None = None
    email: str | None = None
    is_platform_admin: bool
    verified_at: datetime | None = None
    deleted_at: datetime | None = None
    providers: list[str]
    funds_count: int
    last_seen_at: datetime | None = None
    created_at: datetime


class UserListOutAdmin(BaseModel):
    items: list[UserOutAdmin]
    total: int


class UserMembershipOut(BaseModel):
    fund_id: int
    fund_name: str
    role: FundRoleEnum
    status: MemberStatusEnum
    address_unit: str | None = None
    joined_at: datetime | None = None


class UserDetailOutAdmin(UserOutAdmin):
    memberships: list[UserMembershipOut]
    sessions_active: int


# ─── Журнал ───────────────────────────────────────────────────────────────────


class AuditEventOutAdmin(BaseModel):
    id: int
    fund_id: int | None = None
    fund_name: str | None = None
    action: str
    entity: str
    entity_id: int | None = None
    details: dict
    actor_id: int | None = None
    actor_name: str | None = None
    created_at: datetime

"""
Тарифы платформы: действующий тариф фонда и лимит участников.

Купленный тариф действует до plan_expires_at, после — фонд работает на free.
Уже вступившие участники при понижении тарифа не исключаются,
но новых принять нельзя, пока число участников не станет меньше лимита.
"""

from datetime import datetime, timezone

from app.enums import PLAN_MEMBER_LIMITS, PLAN_PRICES_TJS, PlanEnum
from app.models.fund import Fund


def effective_plan(fund: Fund, now: datetime | None = None) -> PlanEnum:
    plan = PlanEnum(fund.plan)
    if plan == PlanEnum.free:
        return plan
    now = now or datetime.now(timezone.utc)
    if fund.plan_expires_at is not None and fund.plan_expires_at <= now:
        return PlanEnum.free
    return plan


def member_limit(fund: Fund, now: datetime | None = None) -> int | None:
    """Лимит участников (включая совет). None — без ограничений."""
    plan = effective_plan(fund, now)
    if plan == PlanEnum.individual:
        return fund.member_limit
    return PLAN_MEMBER_LIMITS[plan]


def plan_price(plan: PlanEnum) -> int | None:
    return PLAN_PRICES_TJS[plan]

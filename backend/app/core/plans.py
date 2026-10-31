"""
Тарифы платформы: действующий тариф фонда, лимит участников и перенос остатка.

Купленный тариф действует до plan_expires_at, после — фонд работает на free.
Уже вступившие участники при понижении тарифа не исключаются,
но новых принять нельзя, пока число участников не станет меньше лимита.

После истечения платного тарифа у фонда 7 дней льготного срока (grace): всё работает,
совет видит предупреждение. Дальше (lapsed), если активных участников больше лимита Free,
жители вносить взносы не могут — только первые 10 членов совета (председатель и самые ранние
администраторы), чтобы лимит нельзя было обойти раздачей прав администратора.

Смена тарифа не сжигает оплаченное: неиспользованный остаток текущего тарифа
переводится в деньги по его цене (fund.plan_price) и докупает дни нового тарифа
по новой цене. Например, осталось 15 дней Max (399 смн/мес) ≈ 199.5 смн →
на Pro (199 смн/мес) это ≈ 30 дней. Продление того же тарифа по той же цене —
просто добавление месяцев к текущей дате окончания.

Цены живут в БД (plan_prices) и меняются админом платформы; fund.plan_price — сколько
фонд реально платит за месяц с учётом скидки, поэтому остаток считается по фактической оплате.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.enums import PLAN_MEMBER_LIMITS, DiscountKindEnum, DiscountStateEnum, LapseEnum, PlanEnum
from app.models.fund import Fund
from app.models.plan_pricing import PlanDiscount

# Длина оплаченного месяца тарифа
PLAN_MONTH = timedelta(days=30)
# Льготный срок после истечения платного тарифа — потом взносы жителей блокируются
PLAN_GRACE = timedelta(days=7)
# За сколько до окончания тарифа совет получает уведомление
PLAN_EXPIRY_WARNING = timedelta(days=3)


@dataclass
class Carryover:
    """Неиспользованный остаток текущего тарифа при переходе на другой."""

    remaining: timedelta  # сколько оставалось текущего тарифа
    value_tjs: float  # его стоимость по цене текущего тарифа
    extra: timedelta | None  # сколько это дней нового тарифа (None — цена нового ещё не известна)


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


def discounted_price(price: int, kind: str, value: int) -> int:
    """Цена за месяц после скидки: целые смн и не ниже 1 — бесплатный месяц только вручную админом."""
    if kind == DiscountKindEnum.percent.value:
        discounted = round(price * (100 - value) / 100)
    else:
        discounted = price - value
    return max(discounted, 1)


def discount_state(discount: PlanDiscount, uses: int, now: datetime | None = None) -> DiscountStateEnum:
    now = now or datetime.now(timezone.utc)
    if not discount.is_active:
        return DiscountStateEnum.disabled
    if discount.ends_at is not None and discount.ends_at <= now:
        return DiscountStateEnum.expired
    if discount.starts_at is not None and discount.starts_at > now:
        return DiscountStateEnum.scheduled
    if discount.max_uses is not None and uses >= discount.max_uses:
        return DiscountStateEnum.exhausted
    return DiscountStateEnum.active


def is_extension(fund: Fund, new_plan: PlanEnum, new_price: int | None, now: datetime) -> bool:
    """Тот же действующий тариф по той же цене — продление от даты окончания."""
    return (
        fund.plan == new_plan.value
        and fund.plan_price == new_price
        and fund.plan_expires_at is not None
        and fund.plan_expires_at > now
    )


def carryover(fund: Fund, new_price: int | None, now: datetime | None = None) -> Carryover | None:
    """
    Остаток текущего оплаченного тарифа в деньгах и в днях нового.

    None — переносить нечего: free, срок истёк, бессрочный тариф (выставлен вручную)
    или цена текущего тарифа неизвестна.
    """
    now = now or datetime.now(timezone.utc)
    if effective_plan(fund, now) == PlanEnum.free or fund.plan_expires_at is None or not fund.plan_price:
        return None

    remaining = fund.plan_expires_at - now
    value_tjs = remaining / PLAN_MONTH * fund.plan_price
    extra = remaining * fund.plan_price / new_price if new_price else None
    return Carryover(remaining=remaining, value_tjs=round(value_tjs, 2), extra=extra)


def lapse_state(fund: Fund, now: datetime | None = None) -> LapseEnum:
    """Состояние фонда после истечения платного тарифа. Бессрочный и free — всегда none."""
    if fund.plan == PlanEnum.free.value or fund.plan_expires_at is None:
        return LapseEnum.none
    now = now or datetime.now(timezone.utc)
    if fund.plan_expires_at > now:
        return LapseEnum.none
    if now < fund.plan_expires_at + PLAN_GRACE:
        return LapseEnum.grace
    return LapseEnum.lapsed


def blocks_at(fund: Fund) -> datetime | None:
    """С какого момента блокируются взносы жителей, если тариф не продлят."""
    if fund.plan == PlanEnum.free.value or fund.plan_expires_at is None:
        return None
    return fund.plan_expires_at + PLAN_GRACE


def free_limit() -> int:
    return PLAN_MEMBER_LIMITS[PlanEnum.free] or 0

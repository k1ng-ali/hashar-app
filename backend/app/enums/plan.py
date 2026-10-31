from enum import Enum


class PlanEnum(str, Enum):
    free = "free"
    pro = "pro"
    max = "max"
    individual = "individual"  # договорной, лимит задаёт админ платформы


class LapseEnum(str, Enum):
    """Состояние фонда после окончания платного тарифа (core/plans.lapse_state)."""

    none = "none"  # free или платный тариф действует
    grace = "grace"  # платный тариф истёк, идёт 7-дневный льготный срок
    lapsed = "lapsed"  # льготный срок прошёл, тариф не продлён


class PlanRequestStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# Лимит участников фонда (включая совет). None — без ограничений
PLAN_MEMBER_LIMITS: dict[PlanEnum, int | None] = {
    PlanEnum.free: 10,
    PlanEnum.pro: 100,
    PlanEnum.max: 500,
    PlanEnum.individual: None,
}


class DiscountKindEnum(str, Enum):
    percent = "percent"  # процент от цены за месяц
    fixed = "fixed"  # смн с цены за месяц


class DiscountStateEnum(str, Enum):
    """Состояние скидки или промокода для админа платформы (core/plans.discount_state)."""

    active = "active"
    scheduled = "scheduled"  # срок ещё не начался
    expired = "expired"  # срок закончился
    exhausted = "exhausted"  # лимит применений исчерпан
    disabled = "disabled"  # выключена админом


class PromoStatusEnum(str, Enum):
    """Что стало с введённым промокодом при расчёте цены."""

    none = "none"  # промокод не вводили
    applied = "applied"
    not_better = "not_better"  # действующая распродажа выгоднее — промокод не расходуется

from enum import Enum


class PlanEnum(str, Enum):
    free = "free"
    pro = "pro"
    max = "max"
    individual = "individual"  # договорной, лимит задаёт админ платформы


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

# Цена в TJS за месяц. None — по договорённости
PLAN_PRICES_TJS: dict[PlanEnum, int | None] = {
    PlanEnum.free: 0,
    PlanEnum.pro: 199,
    PlanEnum.max: 399,
    PlanEnum.individual: None,
}

from enum import Enum


class ContributionCategoryEnum(str, Enum):
    monthly_fee = "monthly_fee"  # ежемесячный обязательный взнос
    target_fund = "target_fund"  # взнос в целевой сбор


class ContributionStatusEnum(str, Enum):
    pending = "pending"  # чек ждёт проверки советом
    approved = "approved"  # деньги зачислены на баланс
    rejected = "rejected"  # чек отклонён с причиной

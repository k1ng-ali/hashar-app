from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import CurrencyEnum, TargetFundCategoryEnum
from app.schemas.contribution import ContributionOut, ReceiptImage


class TargetFundCreateIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=5000)
    target_amount: int = Field(ge=1, le=100_000_000)
    currency: CurrencyEnum
    category: TargetFundCategoryEnum = TargetFundCategoryEnum.landscaping
    # Необязательное фото «на что собираем»: ключ загрузки, как у чека (POST /uploads/receipt)
    image: ReceiptImage | None = None


class TargetFundUpdateIn(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=3, max_length=5000)
    target_amount: int | None = Field(None, ge=1, le=100_000_000)
    category: TargetFundCategoryEnum | None = None
    is_active: bool | None = None
    # Новое фото — ключ загрузки; null — убрать фото. Поле не передано — фото без изменений
    image: ReceiptImage | None = None


class TargetFundOut(BaseModel):
    id: int
    title: str
    description: str
    target_amount: int
    currency: CurrencyEnum
    category: TargetFundCategoryEnum
    is_active: bool
    image: str | None = None  # подписанная ссылка на фото
    collected_amount: int
    remaining_amount: int
    percent: int
    contributors_count: int
    created_at: datetime


class MonthAmountOut(BaseModel):
    period: str  # YYYY-MM
    amount: int


class TargetFundHistoryOut(BaseModel):
    """Строка истории сбора: правка, закрытие или возобновление — кто и когда."""

    action: str  # update / close / open
    # Только для update: поле → [было, стало]; image → "replaced" / "removed"
    changes: dict = Field(default_factory=dict)
    actor_name: str | None = None
    created_at: datetime


class TargetFundDetailOut(TargetFundOut):
    average_contribution: int
    monthly: list[MonthAmountOut]
    # По сбору уже были взносы или расходы: удалить нельзя, только закрыть
    has_operations: bool
    # Публичная история изменений: участники видят, кто и когда менял цель или закрывал сбор
    history: list[TargetFundHistoryOut] = Field(default_factory=list)
    contributions: list[ContributionOut]

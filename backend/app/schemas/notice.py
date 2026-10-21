from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

NoticeKind = Literal["admin_message", "plan_rejected", "plan_approved", "plan_expiring", "plan_expired", "plan_lapsed"]


class NoticeOut(BaseModel):
    id: int
    kind: NoticeKind
    text: str | None = None
    details: dict
    is_unread: bool = False
    created_at: datetime


class NoticeListOut(BaseModel):
    items: list[NoticeOut]
    unread: int


class NoticeIn(BaseModel):
    """Сообщение админа платформы совету фонда."""

    text: str = Field(min_length=3, max_length=1000)


class NoticeOutAdmin(NoticeOut):
    fund_id: int
    fund_name: str
    author_name: str | None = None

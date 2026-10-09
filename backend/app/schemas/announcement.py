from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.enums import AnnouncementCategoryEnum, FundRoleEnum
from app.schemas.account import TransferOut


class AnnouncementCreateIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=5)
    category: Literal[
        AnnouncementCategoryEnum.news,
        AnnouncementCategoryEnum.meeting,
        AnnouncementCategoryEnum.emergency,
        AnnouncementCategoryEnum.cleanup,
    ] = AnnouncementCategoryEnum.news
    is_pinned: bool = False


class CommentCreateIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_unit: str | None = None
    text: str
    created_at: datetime


class AnnouncementOut(BaseModel):
    id: int
    title: str
    content: str
    category: AnnouncementCategoryEnum
    is_pinned: bool
    author_id: int
    author_name: str
    author_role: FundRoleEnum | None = None  # None — автор уже не в фонде
    likes_count: int
    is_liked: bool
    comments: list[CommentOut]
    transfer: TransferOut | None = None
    created_at: datetime

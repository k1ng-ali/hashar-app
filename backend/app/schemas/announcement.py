from datetime import datetime
from pydantic import Field
from backend.app.schemas.base import BaseSchema


class CommentBase(BaseSchema):
    text: str = Field(..., min_length=1, example="Спасибо совету дома за оперативное решение!")


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: str
    announcement_id: str
    user_id: str
    user_name: str
    user_unit: str
    created_at: datetime


class AnnouncementBase(BaseSchema):
    title: str = Field(..., min_length=3, max_length=200, example="Ежемесячный финансовый отчет за Август 2026")
    content: str = Field(..., min_length=5, example="Уважаемые соседи! Публикуем краткие итоги...")
    category: str = Field("Новости", example="Новости")
    is_pinned: bool = False
    image_urls: list[str] = Field(default_factory=list)


class AnnouncementCreate(AnnouncementBase):
    pass


class AnnouncementResponse(AnnouncementBase):
    id: str
    author_id: str
    author_name: str
    author_role: str
    likes_count: int = 0
    liked_by_user_ids: list[str] = Field(default_factory=list)
    comments: list[CommentResponse] = Field(default_factory=list)
    created_at: datetime

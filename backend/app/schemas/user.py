from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import FundRoleEnum


class CurrentUser(BaseModel):
    """Пользователь из access-токена (без похода в БД). Роль в фонде — в FundContext."""

    id: int
    is_platform_admin: bool = False


class UserOut(BaseModel):
    id: int
    full_name: str
    phone: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    is_platform_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DemoMembershipOut(BaseModel):
    fund_name: str
    role: FundRoleEnum


class DemoUserOut(BaseModel):
    """Карточка для быстрого входа в DEV_MODE."""

    id: int
    full_name: str
    avatar_url: str | None = None
    is_platform_admin: bool
    memberships: list[DemoMembershipOut]

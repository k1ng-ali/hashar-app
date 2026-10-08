from datetime import datetime
from pydantic import Field
from backend.app.schemas.base import BaseSchema
from backend.app.models.user import UserRole, UserStatus


class UserBase(BaseSchema):
    phone: str = Field(..., example="+7 (916) 123-45-67")
    full_name: str = Field(..., example="Алексей Николаев")
    address_unit: str = Field(..., example="кв. 15")
    role: UserRole = UserRole.RESIDENT
    status: UserStatus = UserStatus.ACTIVE
    email: str | None = None
    avatar_url: str | None = None


class UserCreate(UserBase):
    id: str | None = None
    password: str | None = None


class UserUpdate(BaseSchema):
    full_name: str | None = None
    phone: str | None = None
    address_unit: str | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    email: str | None = None
    avatar_url: str | None = None


class UserResponse(UserBase):
    id: str
    created_at: datetime


class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseSchema):
    sub: str | None = None

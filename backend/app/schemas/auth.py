from pydantic import BaseModel, Field, model_validator

from app.schemas.user import UserOut


class RegisterIn(BaseModel):
    """Регистрация по паролю. Google / Telegram подключаются позже через user_auth_providers."""

    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = Field(None, min_length=5, max_length=30)
    email: str | None = Field(None, min_length=5, max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6, max_length=64)

    @model_validator(mode="after")
    def check_login(self):
        if not self.phone and not self.email:
            raise ValueError("phone or email is required")
        return self


class LoginIn(BaseModel):
    login: str = Field(min_length=3, max_length=120)  # телефон или email
    password: str = Field(min_length=1, max_length=64)


class DevLoginIn(BaseModel):
    user_id: int


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

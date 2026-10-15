from pydantic import BaseModel, Field, model_validator

from app.core.formatting import format_phone
from app.schemas.user import UserOut


class RegisterIn(BaseModel):
    """Регистрация по паролю. Google / Telegram подключаются позже через user_auth_providers."""

    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = Field(None, max_length=30)
    email: str | None = Field(None, min_length=5, max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6, max_length=64)

    @model_validator(mode="after")
    def check_login(self):
        if self.phone is not None and not self.phone.strip():
            self.phone = None
        if not self.phone and not self.email:
            raise ValueError("phone or email is required")
        if self.phone:
            # Проверка как у реквизитов: код страны и 10–15 цифр (хранится как +цифры для входа)
            format_phone(self.phone)
        return self


class LoginIn(BaseModel):
    login: str = Field(min_length=3, max_length=120)  # телефон или email
    password: str = Field(min_length=1, max_length=64)


class GoogleLoginIn(BaseModel):
    """ID-токен от Google Identity Services (сайт) или нативного входа (Android)."""

    id_token: str = Field(min_length=20, max_length=4096)


class UpdateProfileIn(BaseModel):
    """Смена телефона в профиле. Пустая строка или null — убрать телефон."""

    phone: str | None = Field(None, max_length=30)

    @model_validator(mode="after")
    def check_phone(self):
        if self.phone is not None and not self.phone.strip():
            self.phone = None
        if self.phone:
            format_phone(self.phone)
        return self


class DeleteAccountIn(BaseModel):
    """Подтверждение удаления аккаунта паролем (у аккаунта без пароля — не нужен)."""

    password: str | None = Field(None, max_length=64)


class DevLoginIn(BaseModel):
    user_id: int


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

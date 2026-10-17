from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.core.formatting import format_phone
from app.schemas.user import UserOut


class RegisterIn(BaseModel):
    """
    Регистрация по паролю. Телефон обязателен: по нему подтверждается личность —
    кодом из SMS (+992) или через Google (остальные номера). Email — необязательный второй логин.
    """

    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(max_length=30)
    email: str | None = Field(None, min_length=5, max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6, max_length=64)

    @model_validator(mode="after")
    def check_phone(self):
        # Проверка как у реквизитов: код страны и 10–15 цифр (хранится как +цифры для входа)
        format_phone(self.phone)
        return self


class LoginIn(BaseModel):
    login: str = Field(min_length=3, max_length=120)  # телефон или email
    password: str = Field(min_length=1, max_length=64)


class GoogleLoginIn(BaseModel):
    """ID-токен от Google Identity Services (сайт) или нативного входа (Android)."""

    id_token: str = Field(min_length=20, max_length=4096)


# ─── Подтверждение личности ──────────────────────────────────────────────────

VerificationMethod = Literal["sms", "google"]
VerificationPurpose = Literal["login", "password"]


class ChallengeOut(BaseModel):
    """
    Сессии ещё нет: нужно подтвердить личность одним из methods.

    challenge — токен на 15 минут для /auth/verify/*. phone_hint — номер, куда уйдёт код (скрыт посередине).
    purpose=password — вместе с подтверждением задаётся новый пароль.
    """

    challenge: str
    purpose: VerificationPurpose
    methods: list[VerificationMethod]
    phone_hint: str | None = None


class SmsSendIn(BaseModel):
    challenge: str = Field(min_length=20, max_length=1024)
    # Язык текста SMS
    locale: Literal["tg", "ru", "en"] = "tg"


class SmsSentOut(BaseModel):
    phone_hint: str
    # Через сколько секунд можно запросить новый код и сколько живёт этот
    resend_after: int
    expires_in: int


class _VerifyIn(BaseModel):
    challenge: str = Field(min_length=20, max_length=1024)
    # Обязателен для purpose=password
    new_password: str | None = Field(None, min_length=6, max_length=64)


class SmsVerifyIn(_VerifyIn):
    code: str = Field(pattern=r"^\d{6}$")


class GoogleVerifyIn(_VerifyIn):
    id_token: str = Field(min_length=20, max_length=4096)


class ForgotPasswordIn(BaseModel):
    login: str = Field(min_length=3, max_length=120)  # телефон или email


class UpdateProfileIn(BaseModel):
    """
    Смена телефона в профиле. Пустая строка или null — убрать телефон.
    Новый номер +992 — только с кодом из SMS (POST /auth/me/phone/code).
    """

    phone: str | None = Field(None, max_length=30)
    code: str | None = Field(None, pattern=r"^\d{6}$")

    @model_validator(mode="after")
    def check_phone(self):
        if self.phone is not None and not self.phone.strip():
            self.phone = None
        if self.phone:
            format_phone(self.phone)
        return self


class PhoneCodeIn(BaseModel):
    """Код на новый номер перед сменой телефона."""

    phone: str = Field(max_length=30)
    locale: Literal["tg", "ru", "en"] = "tg"

    @model_validator(mode="after")
    def check_phone(self):
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

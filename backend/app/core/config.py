from datetime import timedelta
from typing import Annotated, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=30)
# Пароль принят — столько есть на подтверждение личности (SMS или Google)
CHALLENGE_TOKEN_EXPIRE = timedelta(minutes=15)
# Подтверждённое устройство не спрашивает подтверждение при входе по паролю
TRUSTED_DEVICE_EXPIRE = timedelta(days=365)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=".env")

    # Подпись JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Cookie с refresh-токеном (в проде только по https)
    COOKIE_SECURE: bool = True
    # lax — фронт и API на одном сайте (hashar.app и api.hashar.app); none — API на чужом домене
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    # Включает /docs, /auth/dev-login, список демо-пользователей и демо-чеки (svg)
    DEV_MODE: bool = False

    # Откуда фронтенду можно ходить к API с cookie; через запятую
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # OAuth-клиенты Google, чьи ID-токены принимает /auth/google (веб и Android), через запятую.
    # Пусто — вход через Google выключен
    GOOGLE_CLIENT_IDS: Annotated[list[str], NoDecode] = []

    # SMS с кодами подтверждения (Payomchi, только номера +992). Пусто — подтверждение по SMS выключено,
    # в DEV_MODE коды пишутся в лог. Sender ID — имя отправителя, одобренное в Payomchi; пусто — по умолчанию
    PAYOMCHI_API_KEY: str = ""
    PAYOMCHI_SENDER_ID: str = ""

    # Максимальный размер тела запроса. Чеки загружаются файлом (/uploads/receipt), но старые
    # версии приложения ещё присылают их data URL внутри JSON — до 6 штук в расходе
    MAX_BODY_BYTES: int = 25 * 1024 * 1024

    # Хранилище чеков по S3 API: в проде Cloudflare R2 (https://<account_id>.r2.cloudflarestorage.com),
    # локально MinIO из docker-compose. Бакет приватный — чеки отдаются ссылками на S3_URL_TTL секунд.
    # Пусто в DEV_MODE — загрузка чеков выключена, работают только демо-чеки
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = ""
    S3_REGION: str = "auto"
    S3_URL_TTL: int = 15 * 60

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    @field_validator("CORS_ORIGINS", "GOOGLE_CLIENT_IDS", mode="before")
    @classmethod
    def split_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def check_production(self):
        # В проде не стартуем с ключом-заглушкой: им можно подделать любой токен
        if not self.DEV_MODE and (len(self.SECRET_KEY) < 32 or self.SECRET_KEY.startswith("change-me")):
            raise ValueError("SECRET_KEY is too weak for production: use `openssl rand -hex 32`")
        # В проде фронтенд только по https. Без CORS_ORIGINS остаются локальные адреса из дефолта,
        # и браузер молча блокирует все запросы с настоящего домена — лучше не стартовать вовсе
        if not self.DEV_MODE:
            bad = [o for o in self.CORS_ORIGINS if not o.startswith("https://") or o == "https://"]
            if bad or not self.CORS_ORIGINS:
                raise ValueError(
                    f"CORS_ORIGINS must list https origins in production (got {self.CORS_ORIGINS}), "
                    "e.g. CORS_ORIGINS=https://hashar.app"
                )
        # Без хранилища в проде нельзя ни прикрепить, ни показать чек
        if not self.DEV_MODE and not self.storage_configured:
            raise ValueError(
                "S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY and S3_BUCKET are required in production"
            )
        return self

    @property
    def storage_configured(self) -> bool:
        return all((self.S3_ENDPOINT_URL, self.S3_ACCESS_KEY_ID, self.S3_SECRET_ACCESS_KEY, self.S3_BUCKET))

    @property
    def get_db_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()

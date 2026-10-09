from datetime import timedelta

from pydantic_settings import BaseSettings, SettingsConfigDict

ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=30)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=".env")

    # Подпись JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Cookie с refresh-токеном (в проде только по https)
    COOKIE_SECURE: bool = True
    # Включает /docs, /auth/dev-login и список демо-пользователей
    DEV_MODE: bool = False

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    @property
    def get_db_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()

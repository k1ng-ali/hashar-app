"""
Пользователь платформы.

Роль и квартира хранятся в членстве фонда (fund_members), а не здесь:
один человек может состоять в нескольких фондах.

- phone / email: логин для входа по паролю (хотя бы одно из двух)
- hashed_password: null, если вход только через провайдера (Google / Telegram)
- is_platform_admin: администратор платформы (подтверждает тарифы)
- verified_at: личность подтверждена кодом из SMS или через Google. Без этого вход не выдаёт сессию
- deleted_at: аккаунт удалён по просьбе пользователя. Строка не удаляется — на неё ссылаются
  взносы, комментарии и журнал фонда, — но имя заменено, а телефон, email, пароль и аватар стёрты
"""

from sqlalchemy import TIMESTAMP, BigInteger, Boolean, Column, ForeignKey, String, UniqueConstraint, func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    full_name = Column(String(120), nullable=False)
    phone = Column(String(30), nullable=True, unique=True, index=True)
    email = Column(String(120), nullable=True, unique=True, index=True)
    avatar_url = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    is_platform_admin = Column(Boolean, nullable=False, default=False, server_default="false")
    verified_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    @property
    def has_password(self) -> bool:
        return self.hashed_password is not None


class UserAuthProvider(Base):
    """
    Внешний способ входа (google / telegram).

    Одна запись на связку провайдер + id пользователя у провайдера (для Google — claim sub).
    """

    __tablename__ = "user_auth_providers"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_user_auth_providers_provider_provider_user_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(20), nullable=False)
    provider_user_id = Column(String(120), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

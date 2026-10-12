"""
Сессия входа — то, на что указывает refresh-токен (sid).

Refresh-токен без сессии бесполезен: выход отзывает сессию, и украденный
токен перестаёт работать сразу, а не через 30 дней.
- expires_at: скользящий срок — продлевается при каждом обновлении токена
- revoked_at: выход из аккаунта (на этом устройстве или везде)
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, String, func

from app.core.database import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_agent = Column(String(255), nullable=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_used_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

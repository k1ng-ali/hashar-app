"""
Подтверждение личности: коды из SMS и подтверждённые устройства.

Новый аккаунт, неподтверждённый аккаунт, вход по паролю с нового устройства и смена пароля
требуют подтверждения: код по SMS (номера +992) или вход через Google.

- VerificationCode: код из SMS. Хранится только HMAC кода (core/security.hash_secret);
  attempts — неверные вводы, после лимита код сгорает; consumed_at — код уже использован
- TrustedDevice: устройство, на котором личность подтверждена. В cookie лежит случайный токен,
  в базе — его HMAC. Выход везде и смена пароля забывают все устройства
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Integer, String, UniqueConstraint, func

from app.core.database import Base


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    phone = Column(String(30), nullable=False)
    code_hash = Column(String(64), nullable=False)
    attempts = Column(Integer, nullable=False, default=0, server_default="0")
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    consumed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class TrustedDevice(Base):
    __tablename__ = "trusted_devices"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_trusted_devices_token_hash"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False)
    user_agent = Column(String(255), nullable=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    last_used_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

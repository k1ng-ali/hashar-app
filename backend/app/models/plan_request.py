"""
Заявка председателя на смену тарифа.

Онлайн-оплаты пока нет: админ платформы подтверждает заявку после оплаты
и включает тариф на указанное число месяцев.
- contact: как связаться с председателем по оплате (телефон, Telegram, email)
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlanRequest(Base):
    __tablename__ = "plan_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    plan = Column(String(20), nullable=False)
    months = Column(Integer, nullable=False, default=1, server_default="1")
    status = Column(String(20), nullable=False, default="pending", server_default="pending", index=True)
    contact = Column(String(150), nullable=False)
    comment = Column(Text, nullable=True)
    admin_comment = Column(Text, nullable=True)
    requested_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    fund = relationship("Fund", lazy="raise")
    requested_by = relationship("User", foreign_keys=[requested_by_id], lazy="raise")

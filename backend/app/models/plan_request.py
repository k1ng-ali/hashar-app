"""
Заявка председателя на смену тарифа.

Онлайн-оплаты пока нет: админ платформы подтверждает заявку после оплаты
и включает тариф на указанное число месяцев.
- contact: как связаться с председателем по оплате (телефон, Telegram, email)
- list_price_tjs / price_tjs: цена за месяц на момент заявки — без скидки и к оплате;
  смена прайса заявку не меняет (у individual пусто: цену вводит админ при подтверждении)
- discount_id / discount_label: применённая скидка и её название или код на момент заявки;
  ожидающие и одобренные заявки расходуют лимит промокода, отказ его возвращает
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlanRequest(Base):
    __tablename__ = "plan_requests"
    # Одна заявка в ожидании на фонд
    __table_args__ = (
        Index("uq_plan_requests_one_pending", "fund_id", unique=True, postgresql_where=text("status = 'pending'")),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    plan = Column(String(20), nullable=False)
    months = Column(Integer, nullable=False, default=1, server_default="1")
    status = Column(String(20), nullable=False, default="pending", server_default="pending", index=True)
    contact = Column(String(150), nullable=False)
    comment = Column(Text, nullable=True)
    list_price_tjs = Column(Integer, nullable=True)
    price_tjs = Column(Integer, nullable=True)
    discount_id = Column(BigInteger, ForeignKey("plan_discounts.id", ondelete="SET NULL"), nullable=True, index=True)
    discount_label = Column(String(100), nullable=True)
    admin_comment = Column(Text, nullable=True)
    requested_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    fund = relationship("Fund", lazy="raise")
    requested_by = relationship("User", foreign_keys=[requested_by_id], lazy="raise")

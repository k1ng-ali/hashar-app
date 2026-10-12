"""
Расход фонда.

- target_fund_id: если указан — расход списан за счёт целевого сбора
- currency: счёт фонда, с которого списаны деньги
- receipt_images: JSON-список data URL чеков / актов выполненных работ
- deleted_at / deleted_by_id: расход отменён председателем. Запись не удаляется —
  остаётся след для ревизии; в остатках, лентах и отчётах отменённые не участвуют
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(30), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, index=True)
    description = Column(Text, nullable=False)
    receipt_images = Column(JSONB, nullable=False, default=list, server_default="[]")
    target_fund_id = Column(BigInteger, ForeignKey("target_funds.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    created_by = relationship("User", foreign_keys=[created_by_id], lazy="raise")
    target_fund = relationship("TargetFund", lazy="raise")

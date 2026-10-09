"""
Взнос жителя с прикреплённым чеком.

- category: monthly_fee / target_fund
- status: pending → approved | rejected (решение принимает совет дома)
- billing_period: месяц ежемесячного взноса (YYYY-MM), для целевых — null
- receipt_image: data URL чека (картинка или svg)
- user_unit: снимок помещения участника на момент взноса
- currency: валюта счёта, на который переведены деньги (из выбранного реквизита)
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Contribution(Base):
    __tablename__ = "contributions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_unit = Column(String(50), nullable=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, index=True)
    requisite_id = Column(BigInteger, ForeignKey("payment_requisites.id", ondelete="SET NULL"), nullable=True)
    category = Column(String(20), nullable=False, default="monthly_fee", server_default="monthly_fee")
    target_fund_id = Column(BigInteger, ForeignKey("target_funds.id", ondelete="SET NULL"), nullable=True, index=True)
    billing_period = Column(String(7), nullable=True)
    receipt_image = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending", server_default="pending", index=True)
    comment_user = Column(Text, nullable=True)
    comment_admin = Column(Text, nullable=True)
    reviewed_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    user = relationship("User", foreign_keys=[user_id], lazy="raise")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id], lazy="raise")
    target_fund = relationship("TargetFund", lazy="raise")

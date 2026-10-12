"""
Банковские реквизиты фонда, которые видят участники при оплате. Каждый реквизит — в своей валюте.

- kind: card — номер карты (16 цифр), account — номер счёта / IBAN
- номер и телефон хранятся в едином формате (core/formatting.py)
"""

from sqlalchemy import TIMESTAMP, BigInteger, Boolean, Column, ForeignKey, String, Text, func

from app.core.database import Base


class PaymentRequisite(Base):
    __tablename__ = "payment_requisites"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    currency = Column(String(3), nullable=False)
    kind = Column(String(10), nullable=False, default="card", server_default="card")
    bank_name = Column(String(100), nullable=False)
    card_or_account_number = Column(String(50), nullable=False)
    recipient_name = Column(String(120), nullable=False)
    phone_number = Column(String(30), nullable=True)
    note = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

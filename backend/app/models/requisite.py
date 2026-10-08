from sqlalchemy import Column, Integer, String, Boolean, Text
from backend.app.core.database import Base


class PaymentRequisite(Base):
    __tablename__ = "payment_requisites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bank_name = Column(String(100), nullable=False)
    card_or_account_number = Column(String(50), nullable=False)
    recipient_name = Column(String(120), nullable=False)
    phone_number = Column(String(30), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    note = Column(Text, nullable=True)

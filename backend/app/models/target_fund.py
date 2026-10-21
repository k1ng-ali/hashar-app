"""
Целевой сбор (краудфандинг дома: шлагбаум, озеленение, капремонт...).

- currency: валюта цели; взносы в сбор принимаются только в ней
- is_active: false — сбор завершён, новые взносы не принимаются
- image: необязательное фото «на что собираем» — ключ в хранилище (core/receipts.py)
"""

from sqlalchemy import TIMESTAMP, BigInteger, Boolean, Column, ForeignKey, Integer, String, Text, func

from app.core.database import Base


class TargetFund(Base):
    __tablename__ = "target_funds"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    target_amount = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False)
    category = Column(String(30), nullable=False, default="landscaping", server_default="landscaping")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    image = Column(Text, nullable=True)
    created_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

"""
Экстренные и полезные телефоны фонда: медпункт, пожарная, диспетчер, директор школы.

Список ведёт совет фонда, участники видят его на доске объявлений.
Телефон хранится в едином формате (core/formatting.py).
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, String, func

from app.core.database import Base


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    created_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

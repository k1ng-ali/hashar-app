"""
Движение между счетами фонда (корректировка).

- перевод: from_* и to_* заполнены (например, 1 000 TJS → 8 500 RUB)
- корректировка: заполнена только одна сторона (списание или зачисление)
Суммы вводит совет вручную — курс платформа не считает.
К каждой записи автоматически публикуется объявление (category=finance).
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AccountTransfer(Base):
    __tablename__ = "account_transfers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    from_currency = Column(String(3), nullable=True)
    from_amount = Column(Integer, nullable=True)
    to_currency = Column(String(3), nullable=True)
    to_amount = Column(Integer, nullable=True)
    comment = Column(Text, nullable=False)
    created_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    created_by = relationship("User", lazy="raise")

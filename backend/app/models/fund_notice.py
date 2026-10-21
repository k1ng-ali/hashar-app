"""
Уведомление совету фонда от платформы.

Видят председатель и администраторы фонда (окно по колокольчику).
- kind: admin_message — текст от админа платформы; plan_rejected / plan_approved — решение по заявке
  на тариф; plan_expiring / plan_expired / plan_lapsed — напоминания об окончании тарифа
- text: текст админа платформы; у системных уведомлений пусто — фронтенд собирает фразу по kind и details
- details: данные для текста (тариф, даты, причина отказа)
- dedupe_key: защита от повторов у автоматических уведомлений (фоновая задача идёт в каждом воркере)
Прочитанность — по fund_members.notices_read_at: всё, что новее, считается непрочитанным.
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class FundNotice(Base):
    __tablename__ = "fund_notices"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_fund_notices_dedupe_key"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(30), nullable=False)
    text = Column(Text, nullable=True)
    details = Column(JSONB, nullable=False, default=dict, server_default="{}")
    author_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    dedupe_key = Column(String(120), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    fund = relationship("Fund", lazy="raise")

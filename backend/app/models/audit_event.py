"""
Журнал действий совета и админа платформы — след для разбора споров.

Записи только добавляются: ни API, ни сервисы их не меняют и не удаляют.
- action: что сделано ("expense.delete", "contribution.approve", "fund.settings" ...)
- entity / entity_id: над чем (тип и id записи)
- details: снимок важных полей на момент действия (суммы, валюты, было → стало)
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=True, index=True)
    actor_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), nullable=False)
    entity = Column(String(30), nullable=False)
    entity_id = Column(BigInteger, nullable=True)
    details = Column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    actor = relationship("User", lazy="raise")

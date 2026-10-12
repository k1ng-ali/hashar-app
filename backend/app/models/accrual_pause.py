"""
Пауза начислений участника — месяцы, за которые совет решил не начислять взнос.

Создаётся только явным решением совета:
- reason=left — при возвращении участника, вышедшего из фонда (период отсутствия);
- reason=blocked — при разблокировке (период блокировки).

Долг за месяцы, когда участник был в фонде, паузой не прощается никогда.
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, String, func

from app.core.database import Base


class MemberAccrualPause(Base):
    __tablename__ = "member_accrual_pauses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(BigInteger, ForeignKey("fund_members.id", ondelete="CASCADE"), nullable=False, index=True)
    from_period = Column(String(7), nullable=False)
    to_period = Column(String(7), nullable=False)
    reason = Column(String(20), nullable=False)
    decided_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

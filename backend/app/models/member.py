"""
Членство пользователя в фонде.

Заявка на вступление — это запись со статусом pending.
- role: resident / admin / chairman (председатель у фонда ровно один)
- status: pending → active | rejected; active → blocked | left; left → pending (возвращение)
- left_at: когда участник вышел; держится до решения совета о возвращении
- blocked_at: когда заблокирован; держится до разблокировки
  (вышедший во время блокировки остаётся blocked с заполненным left_at)
- address_unit: помещение участника в этом фонде ("кв. 12")
- message: сообщение к заявке на вступление
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Index, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import relationship

from app.core.database import Base


class FundMember(Base):
    __tablename__ = "fund_members"
    __table_args__ = (
        UniqueConstraint("fund_id", "user_id", name="uq_fund_members_fund_id_user_id"),
        # Председатель у фонда ровно один — гарантирует сама БД
        Index("uq_fund_members_one_chairman", "fund_id", unique=True, postgresql_where=text("role = 'chairman'")),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="resident", server_default="resident")
    status = Column(String(20), nullable=False, default="pending", server_default="pending", index=True)
    address_unit = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    reviewed_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    joined_at = Column(TIMESTAMP(timezone=True), nullable=True)
    left_at = Column(TIMESTAMP(timezone=True), nullable=True)
    blocked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id], lazy="raise")
    fund = relationship("Fund", lazy="raise")

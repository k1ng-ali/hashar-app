"""
История ежемесячного тарифа фонда.

Запись действует с period (YYYY-MM) и до следующей записи. Каждый месяц
начисляется по тарифу, который действовал именно в нём, поэтому изменение
тарифа не пересчитывает прошлые месяцы. Новый тариф вступает в силу
с 1-го числа следующего месяца.
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Integer, String, UniqueConstraint, func

from app.core.database import Base


class FundRate(Base):
    __tablename__ = "fund_rates"
    __table_args__ = (UniqueConstraint("fund_id", "period", name="uq_fund_rates_fund_id_period"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    period = Column(String(7), nullable=False)
    amount = Column(Integer, nullable=False)
    created_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

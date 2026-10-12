"""
Фонд (дом, ТСЖ, посёлок) и его валютные счета.

- code: публичный код для поиска и ссылки-приглашения (/join/<code>)
- base_currency: валюта ежемесячного тарифа — долги считаются только в ней
- start_period: первый расчётный месяц (YYYY-MM)
- ежемесячный тариф хранится историей в fund_rates (см. models/fund_rate.py)
- plan / plan_expires_at: тариф платформы; после истечения действует free
- member_limit: лимит участников для тарифа individual (null — без ограничений)
- plan_price: цена текущего тарифа в TJS за месяц на момент подключения (у individual — договорная);
  по ней остаток тарифа переводится в дни нового при смене тарифа (core/plans.py)

fund_accounts — по одному счёту на каждую включённую валюту.
Баланс счёта не хранится: считается по взносам, расходам и переводам.
"""

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)

from app.core.database import Base


class Fund(Base):
    __tablename__ = "funds"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    address = Column(String(255), nullable=True)
    code = Column(String(12), nullable=False, unique=True, index=True)
    base_currency = Column(String(3), nullable=False, default="tjs", server_default="tjs")
    start_period = Column(String(7), nullable=False)
    plan = Column(String(20), nullable=False, default="free", server_default="free")
    plan_expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    member_limit = Column(Integer, nullable=True)
    plan_price = Column(Integer, nullable=True)
    created_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class FundAccount(Base):
    __tablename__ = "fund_accounts"
    __table_args__ = (UniqueConstraint("fund_id", "currency", name="uq_fund_accounts_fund_id_currency"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    currency = Column(String(3), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

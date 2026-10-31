"""
Цены платформы: прайс тарифов, скидки и промокоды. Управляет админ платформы.

PlanPrice — текущая цена тарифа за месяц (Free и Individual здесь не хранятся:
первый бесплатный, цену второго админ вводит при подтверждении заявки).
Уже оплаченный срок новая цена не трогает: фонд и заявка хранят свою цену.

PlanDiscount — скидка на месяц тарифа:
- code пуст: распродажа, действует для всех и показывается на витрине
- code задан: промокод, председатель вводит его в заявке
- kind / value: percent — процент, fixed — смн с месяца (итог не ниже 1 смн)
- plans: на какие тарифы действует
- starts_at / ends_at: срок действия (пусто — без ограничения)
- max_months: на сколько оплаченных месяцев действует (пусто — на все в пределах срока);
  месяцы, начинающиеся после ends_at, скидки не получают в любом случае
- max_uses: сколько фондов может применить промокод (пусто — без ограничения)
"""

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    String,
    func,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class PlanPrice(Base):
    __tablename__ = "plan_prices"
    __table_args__ = (CheckConstraint("price_tjs > 0", name="ck_plan_prices_price_positive"),)

    plan = Column(String(20), primary_key=True)
    price_tjs = Column(Integer, nullable=False)
    updated_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class PlanDiscount(Base):
    __tablename__ = "plan_discounts"
    __table_args__ = (
        CheckConstraint("kind IN ('percent', 'fixed')", name="ck_plan_discounts_kind"),
        CheckConstraint("value > 0", name="ck_plan_discounts_value_positive"),
        CheckConstraint("kind <> 'percent' OR value < 100", name="ck_plan_discounts_percent_range"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    code = Column(String(30), nullable=True, unique=True)
    kind = Column(String(10), nullable=False)
    value = Column(Integer, nullable=False)
    plans = Column(JSONB, nullable=False)
    starts_at = Column(TIMESTAMP(timezone=True), nullable=True)
    ends_at = Column(TIMESTAMP(timezone=True), nullable=True)
    max_months = Column(Integer, nullable=True)
    max_uses = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=true())
    created_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

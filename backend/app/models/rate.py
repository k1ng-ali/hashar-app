from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from backend.app.core.database import Base


class BillingRate(Base):
    __tablename__ = "billing_rates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amount = Column(Integer, nullable=False, default=1500)
    effective_from = Column(String(20), nullable=False, default="2026-07-01")
    created_by_admin_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

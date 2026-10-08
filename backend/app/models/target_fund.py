from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from backend.app.core.database import Base


class TargetFund(Base):
    __tablename__ = "target_funds"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    target_amount = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False, default="Благоустройство")
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_admin_id = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

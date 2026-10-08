from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey
from backend.app.core.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, index=True)  # Ремонт, Электрика, Аварийные работы, etc.
    amount = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    receipt_image_paths = Column(JSON, default=list)  # List of URLs or image paths
    target_fund_id = Column(Integer, ForeignKey("target_funds.id", ondelete="SET NULL"), nullable=True)
    target_fund_title = Column(String(200), nullable=True)
    created_by_admin_id = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_admin_name = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

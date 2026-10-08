import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, ForeignKey
from backend.app.core.database import Base


class ContributionCategory(str, enum.Enum):
    MONTHLY_FEE = "MONTHLY_FEE"
    TARGET_FUND = "TARGET_FUND"


class ContributionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Contribution(Base):
    __tablename__ = "contributions"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_name = Column(String(120), nullable=False)
    user_unit = Column(String(50), nullable=False)
    amount = Column(Integer, nullable=False)
    category = Column(Enum(ContributionCategory), default=ContributionCategory.MONTHLY_FEE, nullable=False)
    target_fund_id = Column(Integer, ForeignKey("target_funds.id", ondelete="SET NULL"), nullable=True)
    target_fund_title = Column(String(200), nullable=True)
    billing_period = Column(String(20), nullable=True)  # e.g. "2026-09"
    receipt_image_path = Column(Text, nullable=False)
    status = Column(Enum(ContributionStatus), default=ContributionStatus.PENDING, nullable=False, index=True)
    comment_user = Column(Text, nullable=True)
    comment_admin = Column(Text, nullable=True)
    reviewed_by_admin_id = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_by_admin_name = Column(String(120), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

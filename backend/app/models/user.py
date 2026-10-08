import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum
from backend.app.core.database import Base


class UserRole(str, enum.Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    RESIDENT = "RESIDENT"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    BLOCKED = "BLOCKED"


class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, index=True)
    phone = Column(String(30), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    address_unit = Column(String(50), nullable=False, index=True)  # e.g. "кв. 12"
    role = Column(Enum(UserRole), default=UserRole.RESIDENT, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    email = Column(String(120), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

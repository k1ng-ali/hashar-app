from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), default="Новости", nullable=False)
    image_urls = Column(JSON, default=list)
    is_pinned = Column(Boolean, default=False, nullable=False)
    author_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    author_name = Column(String(120), nullable=False)
    author_role = Column(String(50), default="Совет дома", nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    liked_by_user_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    comments = relationship("AnnouncementComment", back_populates="announcement", cascade="all, delete-orphan")


class AnnouncementComment(Base):
    __tablename__ = "announcement_comments"

    id = Column(String(50), primary_key=True, index=True)
    announcement_id = Column(String(50), ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_name = Column(String(120), nullable=False)
    user_unit = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    announcement = relationship("Announcement", back_populates="comments")

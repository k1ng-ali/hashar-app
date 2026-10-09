"""
Доска объявлений дома.

- announcements: объявление, закрепляет только совет фонда;
  transfer_id — объявление о движении по счетам (создаётся автоматически)
- announcement_comments: комментарии жителей
- announcement_likes: один лайк на пользователя (uq по паре)
"""

from sqlalchemy import TIMESTAMP, BigInteger, Boolean, Column, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fund_id = Column(BigInteger, ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(20), nullable=False, default="news", server_default="news")
    is_pinned = Column(Boolean, nullable=False, default=False, server_default="false")
    author_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    transfer_id = Column(BigInteger, ForeignKey("account_transfers.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    author = relationship("User", lazy="raise")
    transfer = relationship("AccountTransfer", lazy="raise")
    comments = relationship(
        "AnnouncementComment",
        order_by="AnnouncementComment.created_at",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )


class AnnouncementComment(Base):
    __tablename__ = "announcement_comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    announcement_id = Column(BigInteger, ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_unit = Column(String(50), nullable=True)  # снимок помещения автора
    text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", lazy="raise")


class AnnouncementLike(Base):
    __tablename__ = "announcement_likes"
    __table_args__ = (
        UniqueConstraint("announcement_id", "user_id", name="uq_announcement_likes_announcement_id_user_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    announcement_id = Column(BigInteger, ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

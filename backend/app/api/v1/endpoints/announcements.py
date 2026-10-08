import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.announcement import Announcement, AnnouncementComment
from backend.app.models.user import User, UserRole
from backend.app.schemas.announcement import (
    AnnouncementResponse,
    AnnouncementCreate,
    CommentResponse,
    CommentCreate,
)
from backend.app.api.deps import get_current_user, get_current_admin

router = APIRouter()


@router.get("/", response_model=list[AnnouncementResponse])
def get_announcements(db: Session = Depends(get_db)):
    return (
        db.query(Announcement)
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
        .all()
    )


@router.post("/", response_model=AnnouncementResponse)
def create_announcement(
    payload: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # If user wants to pin announcement, they must be admin
    is_pinned = payload.is_pinned
    if is_pinned and current_user.role == UserRole.RESIDENT:
        is_pinned = False

    announcement_id = f"ann_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"
    announcement = Announcement(
        id=announcement_id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
        is_pinned=is_pinned,
        image_urls=payload.image_urls,
        author_id=current_user.id,
        author_name=current_user.full_name,
        author_role="Совет дома" if current_user.role != UserRole.RESIDENT else "Собственник",
        created_at=datetime.now(timezone.utc),
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


@router.post("/{announcement_id}/like", response_model=AnnouncementResponse)
def toggle_like(
    announcement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено")

    liked_users = list(announcement.liked_by_user_ids or [])
    if current_user.id in liked_users:
        liked_users.remove(current_user.id)
        announcement.likes_count = max(0, announcement.likes_count - 1)
    else:
        liked_users.append(current_user.id)
        announcement.likes_count = announcement.likes_count + 1

    announcement.liked_by_user_ids = liked_users
    db.commit()
    db.refresh(announcement)
    return announcement


@router.post("/{announcement_id}/comments", response_model=CommentResponse)
def add_comment(
    announcement_id: str,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено")

    comment_id = f"comm_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"
    comment = AnnouncementComment(
        id=comment_id,
        announcement_id=announcement.id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_unit=current_user.address_unit,
        text=payload.text,
        created_at=datetime.now(timezone.utc),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено")

    if current_user.role == UserRole.RESIDENT and announcement.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для удаления")

    db.delete(announcement)
    db.commit()
    return None

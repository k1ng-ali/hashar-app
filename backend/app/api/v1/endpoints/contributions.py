import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.contribution import Contribution, ContributionStatus, ContributionCategory
from backend.app.models.target_fund import TargetFund
from backend.app.models.user import User
from backend.app.schemas.contribution import (
    ContributionResponse,
    ContributionCreate,
    ContributionVerify,
)
from backend.app.api.deps import get_current_user, get_current_admin

router = APIRouter()


@router.get("/", response_model=list[ContributionResponse])
def get_contributions(
    user_id: Optional[str] = None,
    status: Optional[ContributionStatus] = None,
    category: Optional[ContributionCategory] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Contribution)
    if user_id:
        query = query.filter(Contribution.user_id == user_id)
    if status:
        query = query.filter(Contribution.status == status)
    if category:
        query = query.filter(Contribution.category == category)
    return query.order_by(Contribution.created_at.desc()).all()


@router.get("/pending", response_model=list[ContributionResponse])
def get_pending_contributions(db: Session = Depends(get_db)):
    return (
        db.query(Contribution)
        .filter(Contribution.status == ContributionStatus.PENDING)
        .order_by(Contribution.created_at.desc())
        .all()
    )


@router.post("/", response_model=ContributionResponse)
def create_contribution(
    payload: ContributionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_fund_title = None
    if payload.category == ContributionCategory.TARGET_FUND and payload.target_fund_id:
        tf = db.query(TargetFund).filter(TargetFund.id == payload.target_fund_id).first()
        if not tf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Целевой сбор не найден")
        target_fund_title = tf.title

    contribution_id = f"c_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"
    contribution = Contribution(
        id=contribution_id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_unit=current_user.address_unit,
        amount=payload.amount,
        category=payload.category,
        target_fund_id=payload.target_fund_id,
        target_fund_title=target_fund_title,
        billing_period=payload.billing_period or datetime.now(timezone.utc).strftime("%Y-%m"),
        receipt_image_path=payload.receipt_image_path,
        status=ContributionStatus.PENDING,
        comment_user=payload.comment_user,
        created_at=datetime.now(timezone.utc),
    )
    db.add(contribution)
    db.commit()
    db.refresh(contribution)
    return contribution


@router.post("/{contribution_id}/verify", response_model=ContributionResponse)
def verify_contribution(
    contribution_id: str,
    payload: ContributionVerify,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    contribution = db.query(Contribution).filter(Contribution.id == contribution_id).first()
    if not contribution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись о взносе не найдена")

    contribution.status = payload.status
    contribution.comment_admin = payload.comment_admin
    contribution.reviewed_by_admin_id = admin.id
    contribution.reviewed_by_admin_name = admin.full_name
    contribution.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(contribution)
    return contribution

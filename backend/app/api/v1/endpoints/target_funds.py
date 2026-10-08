from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.target_fund import TargetFund
from backend.app.models.contribution import Contribution, ContributionStatus, ContributionCategory
from backend.app.models.user import User
from backend.app.schemas.target_fund import (
    TargetFundResponse,
    TargetFundCreate,
    TargetFundUpdate,
)
from backend.app.api.deps import get_current_admin

router = APIRouter()


@router.get("/", response_model=list[TargetFundResponse])
def get_target_funds(db: Session = Depends(get_db)):
    funds = db.query(TargetFund).order_by(TargetFund.created_at.desc()).all()
    results = []
    for f in funds:
        collected = (
            db.query(func.coalesce(func.sum(Contribution.amount), 0))
            .filter(
                Contribution.target_fund_id == f.id,
                Contribution.status == ContributionStatus.APPROVED,
            )
            .scalar()
        )
        resp = TargetFundResponse.model_validate(f)
        resp.collected_amount = int(collected)
        results.append(resp)
    return results


@router.post("/", response_model=TargetFundResponse)
def create_target_fund(
    payload: TargetFundCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    target_fund = TargetFund(
        title=payload.title,
        description=payload.description,
        target_amount=payload.target_amount,
        category=payload.category,
        is_active=payload.is_active,
        created_by_admin_id=admin.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(target_fund)
    db.commit()
    db.refresh(target_fund)

    resp = TargetFundResponse.model_validate(target_fund)
    resp.collected_amount = 0
    return resp


@router.put("/{target_fund_id}", response_model=TargetFundResponse)
def update_target_fund(
    target_fund_id: int,
    payload: TargetFundUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    fund = db.query(TargetFund).filter(TargetFund.id == target_fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Целевой сбор не найден")

    if payload.title is not None:
        fund.title = payload.title
    if payload.description is not None:
        fund.description = payload.description
    if payload.target_amount is not None:
        fund.target_amount = payload.target_amount
    if payload.category is not None:
        fund.category = payload.category
    if payload.is_active is not None:
        fund.is_active = payload.is_active

    db.commit()
    db.refresh(fund)

    collected = (
        db.query(func.coalesce(func.sum(Contribution.amount), 0))
        .filter(
            Contribution.target_fund_id == fund.id,
            Contribution.status == ContributionStatus.APPROVED,
        )
        .scalar()
    )
    resp = TargetFundResponse.model_validate(fund)
    resp.collected_amount = int(collected)
    return resp


@router.delete("/{target_fund_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target_fund(
    target_fund_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    fund = db.query(TargetFund).filter(TargetFund.id == target_fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Целевой сбор не найден")
    db.delete(fund)
    db.commit()
    return None

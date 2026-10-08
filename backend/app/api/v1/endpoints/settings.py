from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.rate import BillingRate
from backend.app.models.requisite import PaymentRequisite
from backend.app.models.user import User
from backend.app.schemas.rate import BillingRateResponse, BillingRateCreate
from backend.app.schemas.requisite import PaymentRequisiteResponse, PaymentRequisiteCreate
from backend.app.api.deps import get_current_superadmin

router = APIRouter()


@router.get("/rate", response_model=BillingRateResponse)
def get_current_rate(db: Session = Depends(get_db)):
    rate = db.query(BillingRate).order_by(BillingRate.id.desc()).first()
    if not rate:
        # Create default rate
        rate = BillingRate(amount=1500, effective_from="2026-07-01", created_at=datetime.now(timezone.utc))
        db.add(rate)
        db.commit()
        db.refresh(rate)
    return rate


@router.post("/rate", response_model=BillingRateResponse)
def update_rate(
    payload: BillingRateCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    rate = BillingRate(
        amount=payload.amount,
        effective_from=payload.effective_from,
        created_by_admin_id=admin.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.get("/requisites", response_model=list[PaymentRequisiteResponse])
def get_requisites(db: Session = Depends(get_db)):
    return db.query(PaymentRequisite).all()


@router.post("/requisites", response_model=PaymentRequisiteResponse)
def create_requisite(
    payload: PaymentRequisiteCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    requisite = PaymentRequisite(
        bank_name=payload.bank_name,
        card_or_account_number=payload.card_or_account_number,
        recipient_name=payload.recipient_name,
        phone_number=payload.phone_number,
        is_active=payload.is_active,
        note=payload.note,
    )
    db.add(requisite)
    db.commit()
    db.refresh(requisite)
    return requisite


@router.put("/requisites/{requisite_id}/toggle", response_model=PaymentRequisiteResponse)
def toggle_requisite(
    requisite_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    req = db.query(PaymentRequisite).filter(PaymentRequisite.id == requisite_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Реквизит не найден")
    req.is_active = not req.is_active
    db.commit()
    db.refresh(req)
    return req

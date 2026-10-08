from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.schemas.user import UserResponse, UserCreate, UserUpdate
from backend.app.schemas.summary import ResidentBalanceStatusResponse
from backend.app.api.deps import get_current_user, get_current_superadmin
from backend.app.services.summary_calculator import calculate_resident_status

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.address_unit.asc()).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@router.get("/{user_id}/status", response_model=ResidentBalanceStatusResponse)
def get_resident_status(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return calculate_resident_status(user, db)


@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: str,
    role: UserRole,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    user.role = role
    db.commit()
    db.refresh(user)
    return user

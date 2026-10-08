from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.core.security import create_access_token, verify_password
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.schemas.user import UserResponse, Token
from backend.app.api.deps import get_current_user

router = APIRouter()


class LoginPayload(BaseModel):
    phone_or_email: str
    password: str | None = None


@router.post("/login", response_model=Token)
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    # Find user by phone, email, or unit
    user = (
        db.query(User)
        .filter(
            (User.phone == payload.phone_or_email)
            | (User.email == payload.phone_or_email)
            | (User.id == payload.phone_or_email)
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь с такими данными не найден",
        )

    if user.status == UserStatus.BLOCKED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Учетная запись заблокирована")

    # If user has a password set, verify it
    if user.hashed_password and payload.password:
        if not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный пароль")

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer", user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

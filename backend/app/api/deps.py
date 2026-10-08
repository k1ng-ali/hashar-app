from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.user import User, UserRole, UserStatus

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> User:
    """
    Authenticate user via:
    1. Standard JWT Bearer token
    2. Or X-User-Id header for seamless integration with frontend role switcher
    3. Fallback to Superadmin user for quick local inspection if no auth supplied
    """
    user_id: Optional[str] = None

    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен авторизации",
                headers={"WWW-Authenticate": "Bearer"},
            )
    elif x_user_id:
        user_id = x_user_id

    if not user_id:
        # Check if there is a superadmin or first user in DB as default
        first_user = db.query(User).filter(User.role == UserRole.SUPERADMIN).first()
        if not first_user:
            first_user = db.query(User).first()
        if first_user:
            return first_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.status == UserStatus.BLOCKED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Учетная запись заблокирована")
    return current_user


def get_current_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешен только совету дома (администраторам)",
        )
    return current_user


def get_current_superadmin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешен только председателю дома (суперадминистратору)",
        )
    return current_user

"""
JWT и пароли.

- access-токен живёт 15 минут, передаётся в заголовке Authorization
- refresh-токен живёт 30 дней, лежит в httpOnly cookie и указывает на сессию (sid):
  выход отзывает сессию, и токен сразу перестаёт работать (models/auth_session.py)
"""

from datetime import datetime, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import ACCESS_TOKEN_EXPIRE, REFRESH_TOKEN_EXPIRE, settings

REFRESH_COOKIE_NAME = "refresh_token"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    except ValueError:
        return False


def create_access_token(user_id: int, is_platform_admin: bool = False) -> str:
    # Роли в фондах в токен не кладём — они проверяются по членству на каждый запрос
    payload = {
        "sub": str(user_id),
        "pa": is_platform_admin,
        "type": "access",
        "exp": datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int, session_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "sid": session_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, expected_type: str) -> dict | None:
    """Возвращает payload или None, если токен битый/просрочен/не того типа."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != expected_type or not payload.get("sub"):
        return None
    return payload

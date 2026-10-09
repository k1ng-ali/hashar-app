from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.security import decode_token, hash_password
from app.enums import FundRoleEnum
from app.schemas.auth import LoginIn, RegisterIn
from app.services.announcement_service import AnnouncementService
from app.services.auth_service import AuthService, normalize_phone
from tests.unit.helpers import make_ctx, make_db, make_user


def test_normalize_phone():
    assert normalize_phone("+7 (916) 123-45-67") == "+79161234567"
    assert normalize_phone(None) is None


def test_register_requires_phone_or_email():
    with pytest.raises(ValueError):
        RegisterIn(full_name="Тест", password="secret1")


async def test_register_duplicate_login():
    db = make_db()
    service = AuthService(db=db)
    service.repo.exists_login = AsyncMock(return_value=True)

    with pytest.raises(HTTPException) as exc:
        await service.register(RegisterIn(full_name="Тест", phone="+79000000001", password="secret1"))

    assert exc.value.status_code == 409
    db.commit.assert_not_called()


async def test_login_wrong_password():
    service = AuthService(db=make_db())
    service.repo.get_by_login = AsyncMock(return_value=make_user(hashed_password=hash_password("secret1")))

    with pytest.raises(HTTPException) as exc:
        await service.login(LoginIn(login="+79000000001", password="wrong"))

    assert exc.value.status_code == 401


async def test_login_success_issues_tokens():
    service = AuthService(db=make_db())
    service.repo.get_by_login = AsyncMock(
        return_value=make_user(id=7, is_platform_admin=True, hashed_password=hash_password("secret1"))
    )

    token, refresh_token = await service.login(LoginIn(login="+7 900 000 00 07", password="secret1"))

    access = decode_token(token.access_token, expected_type="access")
    assert access["sub"] == "7"
    assert access["pa"] is True
    assert decode_token(refresh_token, expected_type="refresh")["sub"] == "7"
    # access-токен нельзя использовать как refresh
    assert decode_token(token.access_token, expected_type="refresh") is None
    service.repo.get_by_login.assert_awaited_with("+79000000007")


async def test_refresh_without_cookie():
    service = AuthService(db=make_db())

    with pytest.raises(HTTPException) as exc:
        await service.refresh(refresh_token=None)

    assert exc.value.status_code == 401


async def test_delete_announcement_by_other_resident_forbidden():
    service = AnnouncementService(db=make_db())
    service.repo.get = AsyncMock(return_value=make_user(id=10, author_id=5, transfer_id=None))
    service.repo.delete = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await service.delete(ctx=make_ctx(user_id=3), announcement_id=10)

    assert exc.value.status_code == 403
    service.repo.delete.assert_not_called()


async def test_finance_announcement_cannot_be_deleted():
    service = AnnouncementService(db=make_db())
    service.repo.get = AsyncMock(return_value=make_user(id=10, author_id=1, transfer_id=4))
    service.repo.delete = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await service.delete(ctx=make_ctx(user_id=1, role=FundRoleEnum.chairman), announcement_id=10)

    assert exc.value.status_code == 409
    service.repo.delete.assert_not_called()

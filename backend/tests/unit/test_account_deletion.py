"""Удаление аккаунта: личные данные стираются, записи фондов остаются за «Удалённым пользователем»."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.security import hash_password
from app.schemas.auth import DeleteAccountIn
from app.services import auth_service
from app.services.auth_service import DELETED_USER_NAME, AuthService
from tests.unit.helpers import make_db, make_member, make_user

PASSWORD = "secret-123"


@pytest.fixture(autouse=True)
def reset_limiter():
    auth_service.LOGIN_FAILURES_BY_LOGIN._hits.clear()
    yield
    auth_service.LOGIN_FAILURES_BY_LOGIN._hits.clear()


def deletion_service(user, memberships=(), active_in_fund: int = 1):
    db = make_db()
    service = AuthService(db=db)
    service.repo.get = AsyncMock(return_value=user)
    service.repo.delete_auth_providers = AsyncMock()
    service.member_repo.list_by_user = AsyncMock(return_value=list(memberships))
    service.member_repo.count_active = AsyncMock(return_value=active_in_fund)
    service.session_repo.delete_all = AsyncMock()
    service.plan_request_repo.replace_contact = AsyncMock()
    service.audit.add = lambda **event: service.events.append(event)
    service.events = []
    return db, service


def owner(**extra):
    return make_user(
        id=7,
        email="me@mail.com",
        avatar_url="https://cdn/a.png",
        hashed_password=hash_password(PASSWORD),
        is_platform_admin=True,
        deleted_at=None,
        **extra,
    )


async def test_delete_account_anonymizes_user():
    user = owner()
    db, service = deletion_service(user)

    await service.delete_account(user_id=7, payload=DeleteAccountIn(password=PASSWORD))

    assert user.full_name == DELETED_USER_NAME
    assert (user.phone, user.email, user.avatar_url, user.hashed_password) == (None, None, None, None)
    assert user.is_platform_admin is False
    assert user.deleted_at is not None
    service.session_repo.delete_all.assert_awaited_once_with(user_id=7)
    service.repo.delete_auth_providers.assert_awaited_once_with(user_id=7)
    service.plan_request_repo.replace_contact.assert_awaited_once()
    db.commit.assert_awaited_once()


async def test_delete_account_keeps_unit_and_leaves_funds():
    user = owner()
    active = make_member(id=1, user=user, role="admin", message="Кв. 5, звоните")
    blocked = make_member(id=2, user=user, status="blocked", fund_id=2)
    pending = make_member(id=3, user=user, status="pending", fund_id=3)
    _, service = deletion_service(user, [active, blocked, pending])

    await service.delete_account(user_id=7, payload=DeleteAccountIn(password=PASSWORD))

    assert (active.status, active.role, active.message) == ("left", "resident", None)
    assert active.left_at is not None and active.address_unit == "кв. 1"
    # Заблокированный остаётся заблокированным, как при обычном выходе
    assert blocked.status == "blocked" and blocked.left_at is not None
    assert pending.status == "rejected"
    # Совет фондов видит в журнале, что участник удалил аккаунт
    fund_events = [e for e in service.events if e["action"] == "member.account_deleted"]
    assert {e["fund_id"] for e in fund_events} == {1, 2}


async def test_delete_account_wrong_password():
    user = owner()
    db, service = deletion_service(user)

    with pytest.raises(HTTPException) as exc:
        await service.delete_account(user_id=7, payload=DeleteAccountIn(password="wrong"))

    assert exc.value.status_code == 403
    assert user.full_name == "User 7"
    db.commit.assert_not_awaited()


async def test_delete_account_password_attempts_limited():
    _, service = deletion_service(owner())
    for _ in range(auth_service.LOGIN_FAILURES_BY_LOGIN.limit):
        with pytest.raises(HTTPException):
            await service.delete_account(user_id=7, payload=DeleteAccountIn(password="wrong"))

    with pytest.raises(HTTPException) as exc:
        await service.delete_account(user_id=7, payload=DeleteAccountIn(password=PASSWORD))
    assert exc.value.status_code == 429


async def test_delete_account_chairman_with_members_must_transfer():
    user = owner()
    chairman = make_member(user=user, role="chairman")
    db, service = deletion_service(user, [chairman], active_in_fund=3)

    with pytest.raises(HTTPException) as exc:
        await service.delete_account(user_id=7, payload=DeleteAccountIn(password=PASSWORD))

    assert exc.value.status_code == 409
    assert chairman.role == "chairman" and user.full_name == "User 7"
    db.commit.assert_not_awaited()


async def test_delete_account_sole_chairman_allowed():
    user = owner()
    chairman = make_member(user=user, role="chairman")
    _, service = deletion_service(user, [chairman], active_in_fund=1)

    await service.delete_account(user_id=7, payload=DeleteAccountIn(password=PASSWORD))

    assert (chairman.role, chairman.status) == ("resident", "left")


async def test_delete_account_twice_not_found():
    user = owner()
    _, service = deletion_service(user)
    await service.delete_account(user_id=7, payload=DeleteAccountIn(password=PASSWORD))

    with pytest.raises(HTTPException) as exc:
        await service.delete_account(user_id=7, payload=DeleteAccountIn(password=PASSWORD))
    assert exc.value.status_code == 404

"""Вход через Google и смена телефона в профиле."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jose import jwt
from jose.backends import RSAKey

from app.core import google_auth
from app.core.config import settings
from app.core.google_auth import GoogleTokenError, verify_google_id_token
from app.schemas.auth import GoogleLoginIn, UpdateProfileIn
from app.services import auth_service
from app.services.auth_service import AuthService
from tests.unit.helpers import make_db, make_user

CLIENT_ID = "web-client.apps.googleusercontent.com"
TOKEN = "google-id-token-value"


@pytest.fixture(autouse=True)
def google_settings(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_IDS", [CLIENT_ID])
    for limiter in (auth_service.LOGIN_FAILURES_BY_IP, auth_service.REGISTRATIONS_BY_IP):
        limiter._hits.clear()
    yield
    for limiter in (auth_service.LOGIN_FAILURES_BY_IP, auth_service.REGISTRATIONS_BY_IP):
        limiter._hits.clear()


def claims(**extra):
    data = dict(
        sub="google-42",
        email="Ali@Gmail.com",
        email_verified=True,
        name="Али Валиев",
        picture="https://lh3.googleusercontent.com/a/photo",
    )
    data.update(extra)
    return data


def google_service(monkeypatch, token_claims=None, by_provider=None, by_email=None, error=None):
    async def fake_verify(id_token):
        if error:
            raise error
        return token_claims or claims()

    monkeypatch.setattr(auth_service, "verify_google_id_token", fake_verify)
    db = make_db()
    service = AuthService(db=db)
    service.repo.get_by_provider = AsyncMock(return_value=by_provider)
    service.repo.get_by_email = AsyncMock(return_value=by_email)
    service.repo.create = AsyncMock(side_effect=lambda **fields: make_user(id=99, **fields))
    service.repo.add_auth_provider = MagicMock()
    service.session_repo.create = AsyncMock(return_value=MagicMock(id=1))
    return db, service


# ─── Вход через Google ────────────────────────────────────────────────────────


async def test_google_login_signs_in_linked_user(monkeypatch):
    user = make_user(id=5, email="ali@gmail.com")
    db, service = google_service(monkeypatch, by_provider=user)

    result = await service.google_login(GoogleLoginIn(id_token=TOKEN))
    token, refresh_token = result.token, result.refresh_token
    # Google сам подтверждает личность — устройство сразу подтверждено
    assert result.device_token

    assert token.user.id == 5 and refresh_token
    service.repo.get_by_provider.assert_awaited_once_with("google", "google-42")
    service.repo.add_auth_provider.assert_not_called()
    service.repo.create.assert_not_awaited()
    db.commit.assert_awaited_once()


async def test_google_login_links_existing_account_by_verified_email(monkeypatch):
    user = make_user(id=5, email="ali@gmail.com", avatar_url=None)
    _, service = google_service(monkeypatch, by_email=user)

    token = (await service.google_login(GoogleLoginIn(id_token=TOKEN))).token

    assert token.user.id == 5
    service.repo.get_by_email.assert_awaited_once_with("ali@gmail.com")
    service.repo.add_auth_provider.assert_called_once_with(user_id=5, provider="google", provider_user_id="google-42")
    assert user.avatar_url == "https://lh3.googleusercontent.com/a/photo"


async def test_google_login_creates_account_without_password_and_phone(monkeypatch):
    _, service = google_service(monkeypatch)

    token = (await service.google_login(GoogleLoginIn(id_token=TOKEN))).token

    service.repo.create.assert_awaited_once_with(
        full_name="Али Валиев",
        phone=None,
        email="ali@gmail.com",
        hashed_password=None,
        avatar_url="https://lh3.googleusercontent.com/a/photo",
    )
    service.repo.add_auth_provider.assert_called_once_with(user_id=99, provider="google", provider_user_id="google-42")
    assert token.user.has_password is False and token.user.phone is None


async def test_google_login_ignores_unverified_email(monkeypatch):
    _, service = google_service(monkeypatch, token_claims=claims(email_verified=False, name=""))

    await service.google_login(GoogleLoginIn(id_token=TOKEN))

    # По неподтверждённой почте нельзя ни привязаться к чужому аккаунту, ни занять её
    service.repo.get_by_email.assert_not_awaited()
    fields = service.repo.create.await_args.kwargs
    assert fields["email"] is None and fields["full_name"] == "Google"


async def test_google_login_rejects_invalid_token(monkeypatch):
    db, service = google_service(monkeypatch, error=GoogleTokenError("bad signature"))

    with pytest.raises(HTTPException) as error:
        await service.google_login(GoogleLoginIn(id_token=TOKEN))

    assert error.value.status_code == 401
    db.commit.assert_not_awaited()


async def test_google_login_reports_unreachable_google(monkeypatch):
    _, service = google_service(monkeypatch, error=OSError("timeout"))

    with pytest.raises(HTTPException) as error:
        await service.google_login(GoogleLoginIn(id_token=TOKEN))

    assert error.value.status_code == 503


async def test_google_login_disabled_without_client_ids(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_IDS", [])
    _, service = google_service(monkeypatch)

    with pytest.raises(HTTPException) as error:
        await service.google_login(GoogleLoginIn(id_token=TOKEN))

    assert error.value.status_code == 404


# ─── Проверка ID-токена ───────────────────────────────────────────────────────


@pytest.fixture
def google_keys(monkeypatch):
    """Подменяет открытые ключи Google своей парой RSA; возвращает функцию подписи токена."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    jwk = RSAKey(public_pem, "RS256").to_dict()
    jwk.update(kid="key-1", use="sig")
    downloads = []

    def fake_download():
        downloads.append(1)
        return {"keys": [jwk]}, 3600

    monkeypatch.setattr(google_auth, "_download_certs", fake_download)
    monkeypatch.setattr(google_auth, "_certs", None)

    def sign(**extra):
        payload = dict(iss="https://accounts.google.com", aud=CLIENT_ID, sub="google-42", exp=4_000_000_000)
        payload.update(extra)
        return jwt.encode(payload, private_pem.decode(), algorithm="RS256", headers={"kid": "key-1"})

    sign.downloads = downloads
    return sign


async def test_verify_accepts_valid_token(google_keys):
    result = await verify_google_id_token(google_keys(email="a@b.c"))

    assert result["sub"] == "google-42" and result["email"] == "a@b.c"


async def test_verify_caches_google_keys(google_keys):
    await verify_google_id_token(google_keys())
    await verify_google_id_token(google_keys())

    assert len(google_keys.downloads) == 1


@pytest.mark.parametrize(
    "extra",
    [
        {"aud": "someone-else.apps.googleusercontent.com"},
        {"iss": "https://evil.example.com"},
        {"exp": 1_000_000_000},
    ],
)
async def test_verify_rejects_foreign_or_expired_token(google_keys, extra):
    with pytest.raises(GoogleTokenError):
        await verify_google_id_token(google_keys(**extra))


async def test_verify_rejects_token_signed_by_another_key(google_keys):
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_pem = other_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    forged = jwt.encode(
        {"iss": "accounts.google.com", "aud": CLIENT_ID, "sub": "x", "exp": 4_000_000_000},
        other_pem,
        algorithm="RS256",
        headers={"kid": "key-1"},
    )

    with pytest.raises(GoogleTokenError):
        await verify_google_id_token(forged)


# ─── Смена телефона ───────────────────────────────────────────────────────────


def profile_service(user, phone_taken=False, has_provider=False):
    db = make_db()
    service = AuthService(db=db)
    service.repo.get = AsyncMock(return_value=user)
    service.repo.exists_login = AsyncMock(return_value=phone_taken)
    service.repo.has_auth_provider = AsyncMock(return_value=has_provider)
    service.audit.add = MagicMock()
    return db, service


async def test_update_profile_sets_normalized_phone():
    # Не +992 — SMS туда не доставляются, номер сохраняется без кода (+992 — test_verification.py)
    user = make_user(id=5, phone=None, email="ali@gmail.com", deleted_at=None)
    db, service = profile_service(user)

    result = await service.update_profile(5, UpdateProfileIn(phone="+7 916 123-45-67"))

    assert user.phone == "+79161234567" and result.phone == "+79161234567"
    service.audit.add.assert_called_once()
    db.commit.assert_awaited_once()


async def test_update_profile_rejects_taken_phone():
    user = make_user(id=5, phone=None, deleted_at=None)
    db, service = profile_service(user, phone_taken=True)

    with pytest.raises(HTTPException) as error:
        await service.update_profile(5, UpdateProfileIn(phone="+992 90 123 45 67"))

    assert error.value.status_code == 409 and user.phone is None
    db.commit.assert_not_awaited()


async def test_update_profile_keeps_a_way_to_sign_in():
    # Телефон — единственный логин: email нет, Google не привязан
    user = make_user(id=5, phone="+992901234567", email=None, hashed_password="hash", deleted_at=None)
    _, service = profile_service(user)

    with pytest.raises(HTTPException) as error:
        await service.update_profile(5, UpdateProfileIn(phone=""))

    assert error.value.status_code == 409 and user.phone == "+992901234567"


async def test_update_profile_removes_phone_when_google_is_linked():
    user = make_user(id=5, phone="+992901234567", email=None, deleted_at=None)
    _, service = profile_service(user, has_provider=True)

    await service.update_profile(5, UpdateProfileIn(phone=None))

    assert user.phone is None


def test_update_profile_validates_phone():
    with pytest.raises(ValueError):
        UpdateProfileIn(phone="12")

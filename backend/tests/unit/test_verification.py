"""Подтверждение личности: SMS (Payomchi), Google, подтверждённые устройства и смена пароля."""

import io
import json
import urllib.error
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.core import sms
from app.core.config import settings
from app.core.security import (
    create_challenge_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_secret,
    verify_password,
)
from app.schemas.auth import (
    GoogleVerifyIn,
    LoginIn,
    PhoneCodeIn,
    RegisterIn,
    SmsSendIn,
    SmsVerifyIn,
    UpdateProfileIn,
)
from app.services import auth_service
from app.services.auth_service import AuthService, mask_phone
from tests.unit.helpers import make_db, make_user

TJ_PHONE = "+992901234567"
CODE = "123456"


@pytest.fixture(autouse=True)
def verification_settings(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_IDS", ["web-client"])
    monkeypatch.setattr(settings, "PAYOMCHI_API_KEY", "test-key")
    limiters = (
        auth_service.LOGIN_FAILURES_BY_LOGIN,
        auth_service.LOGIN_FAILURES_BY_IP,
        auth_service.REGISTRATIONS_BY_IP,
        auth_service.SMS_BY_USER,
        auth_service.SMS_BY_IP,
    )
    for limiter in limiters:
        limiter._hits.clear()
    yield
    for limiter in limiters:
        limiter._hits.clear()


def make_service(user=None, google_id=None, device=None, last_code=None):
    db = make_db()
    service = AuthService(db=db)
    service.repo.get = AsyncMock(return_value=user)
    service.repo.get_provider_user_id = AsyncMock(return_value=google_id)
    service.repo.get_by_provider = AsyncMock(return_value=None)
    service.repo.add_auth_provider = MagicMock()
    service.session_repo.create = AsyncMock(return_value=MagicMock(id=1))
    service.session_repo.revoke_all = AsyncMock()
    service.verification_repo.get_device = AsyncMock(return_value=device)
    service.verification_repo.add_device = MagicMock()
    service.verification_repo.delete_devices = AsyncMock()
    service.verification_repo.last_code = AsyncMock(return_value=last_code)
    service.verification_repo.consume_codes = AsyncMock()
    service.verification_repo.create_code = AsyncMock(side_effect=lambda **f: SimpleNamespace(id=77, **f))
    return db, service


def make_code(code=CODE, phone=TJ_PHONE, **extra):
    now = datetime.now(timezone.utc)
    fields = dict(
        phone=phone,
        code_hash=hash_secret(code),
        attempts=0,
        expires_at=now + timedelta(minutes=5),
        consumed_at=None,
        created_at=now - timedelta(minutes=2),
    )
    fields.update(extra)
    return SimpleNamespace(**fields)


def challenge(user_id=1, purpose="login"):
    return create_challenge_token(user_id=user_id, purpose=purpose)


# ─── Вход и регистрация выдают challenge ──────────────────────────────────────


async def test_login_from_new_device_requires_verification():
    user = make_user(phone=TJ_PHONE, hashed_password=hash_password("secret1"))
    db, service = make_service(user=user)
    service.repo.get_by_login = AsyncMock(return_value=user)

    result = await service.login(LoginIn(login=TJ_PHONE, password="secret1"), device_token="unknown-device")

    assert result.token is None and result.refresh_token is None
    assert result.challenge.methods == ["sms"]  # подтверждён по SMS, Google не привязан
    assert result.challenge.phone_hint == "+992 ••• •• 67"
    assert decode_token(result.challenge.challenge, expected_type="challenge")["purpose"] == "login"
    service.session_repo.create.assert_not_awaited()


async def test_unverified_account_requires_verification_even_on_known_device():
    user = make_user(phone=TJ_PHONE, hashed_password=hash_password("secret1"), verified_at=None)
    device = SimpleNamespace(expires_at=datetime.now(timezone.utc) + timedelta(days=1), last_used_at=None)
    _, service = make_service(user=user, device=device)
    service.repo.get_by_login = AsyncMock(return_value=user)

    result = await service.login(LoginIn(login=TJ_PHONE, password="secret1"), device_token="device")

    # Личность ещё не подтверждена: и SMS, и Google
    assert result.challenge.methods == ["sms", "google"]


async def test_register_creates_unverified_account_and_returns_challenge():
    db, service = make_service()
    service.repo.exists_login = AsyncMock(return_value=False)
    service.repo.create = AsyncMock(side_effect=lambda **f: make_user(id=9, verified_at=None, **f))

    result = await service.register(RegisterIn(full_name="Али", phone="+992 90 123 45 67", password="secret1"))

    assert result.token is None
    assert result.challenge.methods == ["sms", "google"]
    db.commit.assert_awaited_once()
    service.session_repo.create.assert_not_awaited()


async def test_foreign_phone_is_verified_only_by_google():
    db, service = make_service()
    service.repo.exists_login = AsyncMock(return_value=False)
    service.repo.create = AsyncMock(side_effect=lambda **f: make_user(id=9, verified_at=None, **f))

    result = await service.register(RegisterIn(full_name="Иван", phone="+7 916 123-45-67", password="secret1"))

    assert result.challenge.methods == ["google"] and result.challenge.phone_hint is None


async def test_no_verification_method_means_no_registration(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_IDS", [])
    db, service = make_service()
    service.repo.exists_login = AsyncMock(return_value=False)
    service.repo.create = AsyncMock(side_effect=lambda **f: make_user(id=9, verified_at=None, **f))

    with pytest.raises(HTTPException) as exc:
        await service.register(RegisterIn(full_name="Иван", phone="+79161234567", password="secret1"))

    assert exc.value.status_code == 503
    db.commit.assert_not_awaited()


async def test_refresh_rejects_unverified_account():
    session = SimpleNamespace(
        id=10, user_id=7, revoked_at=None, expires_at=datetime.now(timezone.utc) + timedelta(days=1), last_used_at=None
    )
    _, service = make_service(user=make_user(id=7, verified_at=None))
    service.session_repo.get = AsyncMock(return_value=session)

    with pytest.raises(HTTPException) as exc:
        await service.refresh(create_refresh_token(user_id=7, session_id=10))

    assert exc.value.detail == "Verification required"


# ─── Отправка кода ────────────────────────────────────────────────────────────


async def test_send_sms_code(monkeypatch):
    sent = []

    async def fake_send(phone, message, idempotency_key):
        sent.append((phone, message, idempotency_key))

    monkeypatch.setattr(auth_service, "send_sms", fake_send)
    db, service = make_service(user=make_user(phone=TJ_PHONE))

    result = await service.send_sms_code(SmsSendIn(challenge=challenge(), locale="ru"), client_ip="1.2.3.4")

    assert result.resend_after == 60 and result.expires_in == 300
    phone, message, key = sent[0]
    code = message.split("код подтверждения ")[1][:6]
    assert phone == TJ_PHONE and code.isdigit() and key == "otp-77"
    # В базе — только HMAC кода
    stored = service.verification_repo.create_code.await_args.kwargs
    assert stored["code_hash"] == hash_secret(code) and code not in stored["code_hash"]
    service.verification_repo.consume_codes.assert_awaited_once()


async def test_send_sms_code_again_too_early_does_not_send(monkeypatch):
    send = AsyncMock()
    monkeypatch.setattr(auth_service, "send_sms", send)
    last = make_code(created_at=datetime.now(timezone.utc) - timedelta(seconds=20))
    _, service = make_service(user=make_user(phone=TJ_PHONE), last_code=last)

    result = await service.send_sms_code(SmsSendIn(challenge=challenge()))

    send.assert_not_awaited()
    assert 0 < result.resend_after <= 41


async def test_send_sms_code_to_foreign_phone_is_refused(monkeypatch):
    monkeypatch.setattr(auth_service, "send_sms", AsyncMock())
    _, service = make_service(user=make_user(phone="+79161234567"))

    with pytest.raises(HTTPException) as exc:
        await service.send_sms_code(SmsSendIn(challenge=challenge()))

    assert exc.value.status_code == 409


async def test_send_sms_code_is_limited_per_account(monkeypatch):
    monkeypatch.setattr(auth_service, "send_sms", AsyncMock())
    _, service = make_service(user=make_user(phone=TJ_PHONE))

    for _ in range(auth_service.SMS_BY_USER.limit):
        await service.send_sms_code(SmsSendIn(challenge=challenge()))
    with pytest.raises(HTTPException) as exc:
        await service.send_sms_code(SmsSendIn(challenge=challenge()))

    assert exc.value.status_code == 429


async def test_send_sms_code_provider_failure(monkeypatch):
    monkeypatch.setattr(auth_service, "send_sms", AsyncMock(side_effect=sms.SmsError("quota")))
    _, service = make_service(user=make_user(phone=TJ_PHONE))
    record = SimpleNamespace(id=77, consumed_at=None)
    service.verification_repo.create_code = AsyncMock(return_value=record)

    with pytest.raises(HTTPException) as exc:
        await service.send_sms_code(SmsSendIn(challenge=challenge()))

    assert exc.value.status_code == 503
    # Неотправленный код гасится — повторить можно сразу
    assert record.consumed_at is not None


async def test_send_sms_code_rejects_bad_challenge():
    _, service = make_service(user=make_user(phone=TJ_PHONE))

    with pytest.raises(HTTPException) as exc:
        await service.send_sms_code(SmsSendIn(challenge=create_refresh_token(user_id=1, session_id=1)))

    assert exc.value.status_code == 401


# ─── Проверка кода ────────────────────────────────────────────────────────────


async def test_verify_sms_issues_session_and_trusts_device():
    user = make_user(phone=TJ_PHONE, verified_at=None)
    code = make_code()
    db, service = make_service(user=user, last_code=code)

    result = await service.verify_sms(SmsVerifyIn(challenge=challenge(), code=CODE))

    assert result.token.user.id == 1 and result.refresh_token and result.device_token
    assert user.verified_at is not None and code.consumed_at is not None
    added = service.verification_repo.add_device.call_args.kwargs
    assert added["token_hash"] == hash_secret(result.device_token)
    db.commit.assert_awaited_once()


async def test_verify_sms_wrong_code_burns_after_attempts():
    code = make_code()
    _, service = make_service(user=make_user(phone=TJ_PHONE), last_code=code)

    for attempt in range(auth_service.SMS_CODE_ATTEMPTS):
        with pytest.raises(HTTPException) as exc:
            await service.verify_sms(SmsVerifyIn(challenge=challenge(), code="000000"))
        assert exc.value.detail == "Invalid code"
    assert code.attempts == auth_service.SMS_CODE_ATTEMPTS and code.consumed_at is not None

    # Даже верный код после этого не подходит
    with pytest.raises(HTTPException) as exc:
        await service.verify_sms(SmsVerifyIn(challenge=challenge(), code=CODE))
    assert exc.value.detail == "Code expired"


@pytest.mark.parametrize(
    "code",
    [
        make_code(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)),
        make_code(consumed_at=datetime.now(timezone.utc)),
        make_code(phone="+992900000000"),  # код ушёл на прежний номер
        None,
    ],
)
async def test_verify_sms_rejects_dead_code(code):
    _, service = make_service(user=make_user(phone=TJ_PHONE), last_code=code)

    with pytest.raises(HTTPException) as exc:
        await service.verify_sms(SmsVerifyIn(challenge=challenge(), code=CODE))

    assert exc.value.detail == "Code expired"


async def test_password_change_requires_new_password():
    _, service = make_service(user=make_user(phone=TJ_PHONE), last_code=make_code())

    with pytest.raises(HTTPException) as exc:
        await service.verify_sms(SmsVerifyIn(challenge=challenge(purpose="password"), code=CODE))

    assert exc.value.status_code == 422


async def test_password_change_after_verification_signs_out_everywhere():
    user = make_user(phone=TJ_PHONE, hashed_password=hash_password("old-pass"))
    _, service = make_service(user=user, last_code=make_code())

    result = await service.verify_sms(
        SmsVerifyIn(challenge=challenge(purpose="password"), code=CODE, new_password="new-pass")
    )

    assert result.token and result.device_token
    service.session_repo.revoke_all.assert_awaited_once()
    service.verification_repo.delete_devices.assert_awaited_once()
    assert verify_password("new-pass", user.hashed_password)


# ─── Подтверждение через Google ───────────────────────────────────────────────


def google_claims(monkeypatch, sub="google-42"):
    async def fake_verify(id_token):
        return {"sub": sub, "email": "ali@gmail.com", "email_verified": True}

    monkeypatch.setattr(auth_service, "verify_google_id_token", fake_verify)


async def test_verify_google_links_google_to_unverified_account(monkeypatch):
    google_claims(monkeypatch)
    user = make_user(phone="+79161234567", verified_at=None)
    _, service = make_service(user=user)

    result = await service.verify_google(GoogleVerifyIn(challenge=challenge(), id_token="x" * 30))

    assert result.token and user.verified_at is not None
    service.repo.add_auth_provider.assert_called_once_with(user_id=1, provider="google", provider_user_id="google-42")


async def test_verify_google_must_match_linked_account(monkeypatch):
    google_claims(monkeypatch, sub="someone-else")
    _, service = make_service(user=make_user(phone="+79161234567"), google_id="google-42")

    with pytest.raises(HTTPException) as exc:
        await service.verify_google(GoogleVerifyIn(challenge=challenge(), id_token="x" * 30))

    assert exc.value.status_code == 403


async def test_verify_google_cannot_replace_sms_for_verified_account(monkeypatch):
    # Укравший пароль не подтвердит вход своим Google, если аккаунт подтверждается по SMS
    google_claims(monkeypatch)
    _, service = make_service(user=make_user(phone=TJ_PHONE), google_id=None)

    with pytest.raises(HTTPException) as exc:
        await service.verify_google(GoogleVerifyIn(challenge=challenge(), id_token="x" * 30))

    assert exc.value.status_code == 409


async def test_verify_google_rejects_google_of_another_user(monkeypatch):
    google_claims(monkeypatch)
    _, service = make_service(user=make_user(phone="+79161234567", verified_at=None))
    service.repo.get_by_provider = AsyncMock(return_value=make_user(id=2))

    with pytest.raises(HTTPException) as exc:
        await service.verify_google(GoogleVerifyIn(challenge=challenge(), id_token="x" * 30))

    assert exc.value.status_code == 409


# ─── Клиент Payomchi ──────────────────────────────────────────────────────────


def test_mask_phone():
    assert mask_phone(TJ_PHONE) == "+992 ••• •• 67"


@pytest.mark.parametrize(
    ("phone", "expected"),
    [(TJ_PHONE, True), ("+79161234567", False), ("+99290123456", False), (None, False)],
)
def test_is_sms_phone(phone, expected):
    assert sms.is_sms_phone(phone) is expected


def test_payomchi_request(monkeypatch):
    monkeypatch.setattr(settings, "PAYOMCHI_SENDER_ID", "HASHAR")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(request, timeout):
        captured["request"] = request
        return FakeResponse()

    monkeypatch.setattr(sms.urllib.request, "urlopen", fake_urlopen)

    sms._post(TJ_PHONE, "code 123456", "otp-1")

    request = captured["request"]
    assert request.full_url == sms.PAYOMCHI_SMS_URL
    assert request.get_header("X-api-key") == "test-key"
    assert request.get_header("Idempotency-key") == "otp-1"
    # Только цифры, без «+»
    assert json.loads(request.data) == {
        "phone": "992901234567",
        "message": "code 123456",
        "channel": "sms",
        "senderId": "HASHAR",
    }


@pytest.mark.parametrize(("status_code", "error"), [(400, sms.SmsRejectedPhone), (403, sms.SmsError), (409, None)])
def test_payomchi_errors(monkeypatch, status_code, error):
    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(request.full_url, status_code, "error", {}, io.BytesIO(b'{"code":"x"}'))

    monkeypatch.setattr(sms.urllib.request, "urlopen", fake_urlopen)

    if error is None:
        # 409 — этот Idempotency-Key уже обработан, SMS уже отправлено
        sms._post(TJ_PHONE, "code", "otp-1")
    else:
        with pytest.raises(error):
            sms._post(TJ_PHONE, "code", "otp-1")


# ─── Смена телефона ───────────────────────────────────────────────────────────


def phone_service(user, last_code=None, phone_taken=False):
    db, service = make_service(user=user, last_code=last_code)
    service.repo.exists_login = AsyncMock(return_value=phone_taken)
    service.repo.has_auth_provider = AsyncMock(return_value=False)
    service.audit.add = MagicMock()
    return db, service


async def test_new_tj_phone_requires_code():
    user = make_user(phone="+79161234567")
    db, service = phone_service(user)

    with pytest.raises(HTTPException) as exc:
        await service.update_profile(1, UpdateProfileIn(phone=TJ_PHONE))

    assert exc.value.detail == "Phone confirmation required" and user.phone == "+79161234567"
    db.commit.assert_not_awaited()


async def test_new_tj_phone_with_code_is_saved():
    user = make_user(phone="+79161234567")
    code = make_code(phone=TJ_PHONE)
    db, service = phone_service(user, last_code=code)

    result = await service.update_profile(1, UpdateProfileIn(phone=TJ_PHONE, code=CODE))

    assert result.phone == TJ_PHONE and code.consumed_at is not None
    db.commit.assert_awaited_once()


@pytest.mark.parametrize(
    ("code", "detail"),
    [
        (make_code(phone=TJ_PHONE), "Invalid code"),
        # Код подтверждал другой номер — для этого не годится
        (make_code(phone="+992900000000", code="000000"), "Code expired"),
    ],
)
async def test_new_tj_phone_with_wrong_code_is_rejected(code, detail):
    user = make_user(phone="+79161234567")
    _, service = phone_service(user, last_code=code)

    with pytest.raises(HTTPException) as exc:
        await service.update_profile(1, UpdateProfileIn(phone=TJ_PHONE, code="000000"))

    assert exc.value.detail == detail and user.phone == "+79161234567"


async def test_send_phone_code_to_new_number(monkeypatch):
    send = AsyncMock()
    monkeypatch.setattr(auth_service, "send_sms", send)
    _, service = phone_service(make_user(phone="+79161234567"))

    result = await service.send_phone_code(1, PhoneCodeIn(phone="+992 90 123 45 67"))

    assert result.phone_hint == "+992 ••• •• 67"
    assert send.await_args.args[0] == TJ_PHONE
    assert service.verification_repo.create_code.await_args.kwargs["phone"] == TJ_PHONE


@pytest.mark.parametrize(
    ("phone", "taken"),
    [("+992 90 123 45 67", True), ("+7 916 000-00-00", False)],
)
async def test_send_phone_code_refused(monkeypatch, phone, taken):
    send = AsyncMock()
    monkeypatch.setattr(auth_service, "send_sms", send)
    _, service = phone_service(make_user(phone="+79161234567"), phone_taken=taken)

    with pytest.raises(HTTPException) as exc:
        await service.send_phone_code(1, PhoneCodeIn(phone=phone))

    assert exc.value.status_code == 409
    send.assert_not_awaited()

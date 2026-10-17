import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import REFRESH_TOKEN_EXPIRE, TRUSTED_DEVICE_EXPIRE, settings
from app.core.google_auth import GoogleTokenError, verify_google_id_token
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import (
    create_access_token,
    create_challenge_token,
    create_refresh_token,
    decode_token,
    generate_device_token,
    generate_sms_code,
    hash_password,
    hash_secret,
    verify_password,
)
from app.core.sms import SmsError, SmsRejectedPhone, is_sms_phone, send_sms, sms_enabled
from app.enums import FundRoleEnum, MemberStatusEnum
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.auth_session_repo import AuthSessionRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.plan_request_repo import PlanRequestRepository
from app.repositories.user_repo import UserRepository
from app.repositories.verification_repo import VerificationRepository
from app.schemas.auth import (
    ChallengeOut,
    DeleteAccountIn,
    ForgotPasswordIn,
    GoogleLoginIn,
    GoogleVerifyIn,
    LoginIn,
    PhoneCodeIn,
    RegisterIn,
    SmsSendIn,
    SmsSentOut,
    SmsVerifyIn,
    TokenOut,
    UpdateProfileIn,
)
from app.schemas.user import DemoMembershipOut, DemoUserOut, UserOut

# Неудачные входы: по логину — от перебора пароля одного человека,
# по IP — от перебора многих логинов с одного адреса. Неверные коды из SMS считаются по IP туда же
LOGIN_FAILURES_BY_LOGIN = SlidingWindowLimiter(limit=10, window_seconds=15 * 60)
LOGIN_FAILURES_BY_IP = SlidingWindowLimiter(limit=50, window_seconds=15 * 60)
REGISTRATIONS_BY_IP = SlidingWindowLimiter(limit=10, window_seconds=60 * 60)
# Каждое SMS платное: на аккаунт и на адрес в час
SMS_BY_USER = SlidingWindowLimiter(limit=5, window_seconds=60 * 60)
SMS_BY_IP = SlidingWindowLimiter(limit=20, window_seconds=60 * 60)

SMS_CODE_TTL = timedelta(minutes=5)
SMS_RESEND_SECONDS = 60
# Столько неверных вводов — и код сгорает, нужен новый
SMS_CODE_ATTEMPTS = 5
SMS_TEXTS = {
    "tg": "Ҳашар: рамзи тасдиқ {code}. Ба касе нагӯед.",
    "ru": "Ҳашар: код подтверждения {code}. Никому не сообщайте.",
    "en": "Hashar: your verification code is {code}. Do not share it.",
}

# Длина User-Agent, которую сохраняем в сессии
USER_AGENT_LENGTH = 255

GOOGLE_PROVIDER = "google"
# Ограничения колонок users: имя и ссылка на аватар от Google длиннее не сохраняются
FULL_NAME_LENGTH = 120
AVATAR_URL_LENGTH = 255

# Чем заменяются имя удалённого пользователя и его контакт в заявках на тариф
DELETED_USER_NAME = "Удалённый пользователь"
DELETED_CONTACT = "—"


def normalize_phone(phone: str | None) -> str | None:
    """«+7 (916) 123-45-67» → «+79161234567»."""
    if not phone:
        return None
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"+{digits}" if digits else None


def mask_phone(phone: str) -> str:
    """«+992901234567» → «+992 ••• •• 67»: видно, на какой номер ушёл код, но не весь номер."""
    return f"{phone[:4]} ••• •• {phone[-2:]}"


def _too_many_attempts() -> HTTPException:
    return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts, try later")


@dataclass
class AuthResult:
    """
    Итог входа: либо сессия (token + refresh_token), либо challenge — сначала подтвердить личность.
    device_token — устройство только что подтверждено, его кладут в cookie.
    """

    token: TokenOut | None = None
    refresh_token: str | None = None
    device_token: str | None = None
    challenge: ChallengeOut | None = None


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db=db)
        self.member_repo = MemberRepository(db=db)
        self.session_repo = AuthSessionRepository(db=db)
        self.plan_request_repo = PlanRequestRepository(db=db)
        self.audit = AuditRepository(db=db)
        self.verification_repo = VerificationRepository(db=db)

    async def register(self, payload: RegisterIn, client_ip: str | None = None) -> AuthResult:
        """Аккаунт создаётся неподтверждённым: сессию выдаст подтверждение личности (SMS или Google)."""
        ip_key = client_ip or "unknown"
        if REGISTRATIONS_BY_IP.is_blocked(ip_key):
            raise _too_many_attempts()
        REGISTRATIONS_BY_IP.hit(ip_key)

        phone = normalize_phone(payload.phone)
        email = payload.email.strip().lower() if payload.email else None
        if await self.repo.exists_login(phone=phone, email=email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone or email is already registered")

        user = await self.repo.create(
            full_name=payload.full_name.strip(),
            phone=phone,
            email=email,
            hashed_password=hash_password(payload.password),
        )
        challenge = await self._challenge(user, purpose="login")
        await self.db.commit()
        return AuthResult(challenge=challenge)

    async def login(
        self,
        payload: LoginIn,
        client_ip: str | None = None,
        user_agent: str | None = None,
        device_token: str | None = None,
    ) -> AuthResult:
        """Сессия — только подтверждённому аккаунту на подтверждённом устройстве, иначе challenge."""
        login = payload.login.strip()
        login = normalize_phone(login) if "@" not in login else login.lower()
        login_key, ip_key = login or "", client_ip or "unknown"
        # Проверяем до bcrypt: заблокированный перебор не должен грузить процессор
        if LOGIN_FAILURES_BY_LOGIN.is_blocked(login_key) or LOGIN_FAILURES_BY_IP.is_blocked(ip_key):
            raise _too_many_attempts()

        user = await self.repo.get_by_login(login)
        if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
            LOGIN_FAILURES_BY_LOGIN.hit(login_key)
            LOGIN_FAILURES_BY_IP.hit(ip_key)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login or password")

        LOGIN_FAILURES_BY_LOGIN.reset(login_key)
        if user.verified_at is None or not await self._is_trusted_device(user.id, device_token):
            return AuthResult(challenge=await self._challenge(user, purpose="login"))

        token, refresh_token = await self._start_session(user, user_agent)
        await self.db.commit()
        return AuthResult(token=token, refresh_token=refresh_token)

    async def google_login(
        self,
        payload: GoogleLoginIn,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResult:
        """
        Вход через Google, он же регистрация.

        1. Аккаунт, уже привязанный к этому Google-аккаунту (sub), — входим в него.
        2. Иначе аккаунт с тем же email — Google подтвердил, что почта принадлежит этому человеку,
           привязываем Google к нему (вход по паролю тоже остаётся).
        3. Иначе создаём новый аккаунт без пароля и телефона: телефон добавляется в профиле.

        Вход через Google сам подтверждает личность, поэтому устройство сразу становится подтверждённым.
        """
        if not settings.GOOGLE_CLIENT_IDS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Google sign-in is disabled")
        ip_key = client_ip or "unknown"
        claims = await self._google_claims(payload.id_token, ip_key)

        google_id = str(claims["sub"])
        # Неподтверждённому email не доверяем: по нему нельзя ни привязать, ни занять почту
        email = str(claims["email"]).strip().lower() if claims.get("email") and claims.get("email_verified") else None
        picture = claims.get("picture")
        picture = picture if isinstance(picture, str) and len(picture) <= AVATAR_URL_LENGTH else None

        user = await self.repo.get_by_provider(GOOGLE_PROVIDER, google_id)
        if not user and email:
            user = await self.repo.get_by_email(email)
            if user:
                self.repo.add_auth_provider(user_id=user.id, provider=GOOGLE_PROVIDER, provider_user_id=google_id)
                if not user.avatar_url:
                    user.avatar_url = picture
        if not user:
            if REGISTRATIONS_BY_IP.is_blocked(ip_key):
                raise _too_many_attempts()
            REGISTRATIONS_BY_IP.hit(ip_key)
            name = str(claims.get("name") or "").strip() or (email.split("@")[0] if email else "Google")
            user = await self.repo.create(
                full_name=name[:FULL_NAME_LENGTH],
                phone=None,
                email=email,
                hashed_password=None,
                avatar_url=picture,
            )
            self.repo.add_auth_provider(user_id=user.id, provider=GOOGLE_PROVIDER, provider_user_id=google_id)

        return await self._complete_verification(user, purpose="login", new_password=None, user_agent=user_agent)

    # ─── Подтверждение личности ────────────────────────────────────────────────

    async def forgot_password(self, payload: ForgotPasswordIn, client_ip: str | None = None) -> ChallengeOut:
        """Сброс пароля: подтвердить личность и задать новый пароль (/auth/verify/* с new_password)."""
        login = payload.login.strip()
        login = normalize_phone(login) if "@" not in login else login.lower()
        ip_key = client_ip or "unknown"
        if LOGIN_FAILURES_BY_IP.is_blocked(ip_key):
            raise _too_many_attempts()

        user = await self.repo.get_by_login(login or "")
        if not user or user.deleted_at is not None:
            LOGIN_FAILURES_BY_IP.hit(ip_key)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return await self._challenge(user, purpose="password")

    async def password_challenge(self, user_id: int) -> ChallengeOut:
        """Смена пароля из профиля — тоже только после повторного подтверждения личности."""
        user = await self.repo.get(user_id)
        if not user or user.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return await self._challenge(user, purpose="password")

    async def send_sms_code(self, payload: SmsSendIn, client_ip: str | None = None) -> SmsSentOut:
        """Код из SMS на телефон аккаунта — для подтверждения личности."""
        user, _ = await self._load_challenge(payload.challenge)
        if not self._phone_needs_code(user.phone):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SMS is unavailable for this phone")
        return await self._send_code(user.id, user.phone, payload.locale, client_ip)

    async def verify_sms(
        self, payload: SmsVerifyIn, client_ip: str | None = None, user_agent: str | None = None
    ) -> AuthResult:
        user, purpose = await self._load_challenge(payload.challenge, for_update=True)
        self._check_new_password(purpose, payload.new_password)
        await self._consume_code(user.id, user.phone, payload.code, client_ip)
        return await self._complete_verification(user, purpose, payload.new_password, user_agent)

    async def verify_google(
        self, payload: GoogleVerifyIn, client_ip: str | None = None, user_agent: str | None = None
    ) -> AuthResult:
        """
        Подтверждение через Google. Уже привязанный Google должен совпасть. Новый привязывается,
        только пока Google есть в methods (см. _methods): иначе укравший пароль привязал бы свой.
        """
        user, purpose = await self._load_challenge(payload.challenge, for_update=True)
        self._check_new_password(purpose, payload.new_password)
        if "google" not in await self._methods(user):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Google verification is unavailable")
        ip_key = client_ip or "unknown"
        claims = await self._google_claims(payload.id_token, ip_key)

        google_id = str(claims["sub"])
        linked_id = await self.repo.get_provider_user_id(user.id, GOOGLE_PROVIDER)
        if linked_id and linked_id != google_id:
            LOGIN_FAILURES_BY_IP.hit(ip_key)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Google account does not match")
        if not linked_id:
            owner = await self.repo.get_by_provider(GOOGLE_PROVIDER, google_id)
            if owner and owner.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Google account is linked to another user"
                )
            self.repo.add_auth_provider(user_id=user.id, provider=GOOGLE_PROVIDER, provider_user_id=google_id)
            picture = claims.get("picture")
            if not user.avatar_url and isinstance(picture, str) and len(picture) <= AVATAR_URL_LENGTH:
                user.avatar_url = picture

        return await self._complete_verification(user, purpose, payload.new_password, user_agent)

    async def refresh(self, refresh_token: str | None) -> tuple[TokenOut, str]:
        """Новый access-токен по живой сессии; срок сессии продлевается (скользящий)."""
        session, user = await self._active_session(refresh_token)
        if not session or not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        # Сессии, открытые до подтверждения личности, не продлеваем: пусть войдёт заново и подтвердит
        if user.verified_at is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verification required")

        now = datetime.now(timezone.utc)
        session.last_used_at = now
        session.expires_at = now + REFRESH_TOKEN_EXPIRE
        await self.db.commit()
        return self._issue_tokens(user, session.id)

    async def logout(self, refresh_token: str | None) -> None:
        """Отзывает сессию из cookie. Битый или чужой токен — просто ничего не делаем."""
        session, _ = await self._active_session(refresh_token)
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def logout_all(self, user_id: int) -> None:
        """
        Выход на всех устройствах: украденный refresh-токен больше не сработает,
        а устройства забываются — вход по паролю снова потребует подтверждения.
        """
        await self.session_repo.revoke_all(user_id=user_id, now=datetime.now(timezone.utc))
        await self.verification_repo.delete_devices(user_id)
        await self.db.commit()

    async def me(self, user_id: int) -> UserOut:
        user = await self.repo.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserOut.model_validate(user)

    async def send_phone_code(self, user_id: int, payload: PhoneCodeIn, client_ip: str | None = None) -> SmsSentOut:
        """Код на новый номер +992 перед сменой телефона: номер должен принадлежать владельцу аккаунта."""
        user = await self.repo.get(user_id)
        if not user or user.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        phone = normalize_phone(payload.phone)
        if not self._phone_needs_code(phone):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SMS is unavailable for this phone")
        if phone != user.phone and await self.repo.exists_login(phone=phone, email=None):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone is already registered")
        return await self._send_code(user.id, phone, payload.locale, client_ip)

    async def update_profile(self, user_id: int, payload: UpdateProfileIn, client_ip: str | None = None) -> UserOut:
        """
        Смена телефона. Он же логин для входа по паролю, поэтому должен быть свободен.
        Номер +992 подтверждается кодом из SMS (send_phone_code): по телефону подтверждается
        личность, и чужой номер дал бы его владельцу войти в этот аккаунт.
        """
        user = await self.repo.get(user_id, for_update=True)
        if not user or user.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        phone = normalize_phone(payload.phone)
        if phone == user.phone:
            return UserOut.model_validate(user)
        if phone and await self.repo.exists_login(phone=phone, email=None):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone is already registered")
        # Без телефона должен остаться способ войти: email с паролем или Google
        if not phone and not (user.email and user.hashed_password) and not await self.repo.has_auth_provider(user_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone is the only way to sign in")
        if self._phone_needs_code(phone):
            if not payload.code:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone confirmation required")
            await self._consume_code(user.id, phone, payload.code, client_ip)

        user.phone = phone
        self.audit.add(fund_id=None, actor_id=user_id, action="user.phone_change", entity="user", entity_id=user_id)
        await self.db.commit()
        return UserOut.model_validate(user)

    # ─── Удаление аккаунта ─────────────────────────────────────────────────────

    async def delete_account(self, user_id: int, payload: DeleteAccountIn) -> None:
        """
        Удаление аккаунта с обезличиванием: личные данные стираются, записи фондов остаются.

        Взносы (с чеками), комментарии, объявления и журнал — это учёт фонда, его видят
        и проверяют другие участники, поэтому строки не удаляются: они остаются за
        «Удалённым пользователем» с помещением, а имя, телефон, email, пароль, аватар,
        сессии входа и способы входа стираются. Войти в аккаунт больше нельзя, телефон
        и email освобождаются для новой регистрации.

        Председатель фонда, где есть другие участники, сначала передаёт права —
        как при выходе из фонда. Если он в фонде один, фонд просто остаётся без участников.
        """
        user = await self.repo.get(user_id, for_update=True)
        if not user or user.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Пароль подтверждает, что это владелец, а не тот, кто взял разблокированный телефон.
        # 403, а не 401: на 401 фронтенд пытается обновить токен
        limiter_key = f"delete:{user_id}"
        if LOGIN_FAILURES_BY_LOGIN.is_blocked(limiter_key):
            raise _too_many_attempts()
        if user.hashed_password and not verify_password(payload.password or "", user.hashed_password):
            LOGIN_FAILURES_BY_LOGIN.hit(limiter_key)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")

        memberships = await self.member_repo.list_by_user(user_id)
        for member in memberships:
            if member.role == FundRoleEnum.chairman.value and await self.member_repo.count_active(member.fund_id) > 1:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Transfer chairman rights first")

        now = datetime.now(timezone.utc)
        for member in memberships:
            if member.status in (MemberStatusEnum.active.value, MemberStatusEnum.blocked.value):
                # Как выход из фонда: заблокированный остаётся заблокированным с датой выхода
                member.left_at = now
                if member.status == MemberStatusEnum.active.value:
                    member.status = MemberStatusEnum.left.value
                self.audit.add(
                    fund_id=member.fund_id,
                    actor_id=user_id,
                    action="member.account_deleted",
                    entity="member",
                    entity_id=member.id,
                    details={"unit": member.address_unit},
                )
            elif member.status == MemberStatusEnum.pending.value:
                member.status = MemberStatusEnum.rejected.value
            # Помещение остаётся: по нему совет сверяет взносы и долги
            member.role = FundRoleEnum.resident.value
            member.message = None

        await self.plan_request_repo.replace_contact(user_id=user_id, contact=DELETED_CONTACT)
        await self.session_repo.delete_all(user_id=user_id)
        await self.verification_repo.delete_all(user_id=user_id)
        await self.repo.delete_auth_providers(user_id=user_id)

        user.full_name = DELETED_USER_NAME
        user.phone = None
        user.email = None
        user.avatar_url = None
        user.hashed_password = None
        user.is_platform_admin = False
        user.deleted_at = now
        self.audit.add(fund_id=None, actor_id=user_id, action="user.delete", entity="user", entity_id=user_id)
        await self.db.commit()

    # ─── DEV_MODE ──────────────────────────────────────────────────────────────

    async def dev_login(self, user_id: int, user_agent: str | None = None) -> tuple[TokenOut, str]:
        self._ensure_dev_mode()
        user = await self.repo.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        # Демо-пользователи считаются подтверждёнными, иначе refresh выкинет их из сессии
        user.verified_at = user.verified_at or datetime.now(timezone.utc)
        result = await self._start_session(user, user_agent)
        await self.db.commit()
        return result

    async def list_demo_users(self) -> list[DemoUserOut]:
        self._ensure_dev_mode()
        users = await self.repo.list_all()
        result = []
        for user in users:
            memberships = await self.member_repo.list_by_user(user.id)
            result.append(
                DemoUserOut(
                    id=user.id,
                    full_name=user.full_name,
                    avatar_url=user.avatar_url,
                    is_platform_admin=user.is_platform_admin,
                    memberships=[
                        DemoMembershipOut(fund_name=m.fund.name, role=m.role)
                        for m in memberships
                        if m.status == "active"
                    ],
                )
            )
        return result

    # ─── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _phone_needs_code(phone: str | None) -> bool:
        """Номер, который подтверждается кодом из SMS: +992, если SMS включены."""
        return sms_enabled() and is_sms_phone(phone)

    async def _send_code(self, user_id: int, phone: str, locale: str, client_ip: str | None) -> SmsSentOut:
        """
        Код из SMS на phone. Новый код отменяет прежний. Повторный запрос на тот же номер раньше
        SMS_RESEND_SECONDS ничего не отправляет и говорит, сколько ждать.
        """
        phone_hint = mask_phone(phone)
        now = datetime.now(timezone.utc)
        last = await self.verification_repo.last_code(user_id)
        if last and last.consumed_at is None and last.phone == phone:
            passed = (now - last.created_at).total_seconds()
            if passed < SMS_RESEND_SECONDS:
                return SmsSentOut(
                    phone_hint=phone_hint,
                    resend_after=int(SMS_RESEND_SECONDS - passed) + 1,
                    expires_in=max(int((last.expires_at - now).total_seconds()), 0),
                )

        user_key, ip_key = str(user_id), client_ip or "unknown"
        if SMS_BY_USER.is_blocked(user_key) or SMS_BY_IP.is_blocked(ip_key):
            raise _too_many_attempts()

        code = generate_sms_code()
        await self.verification_repo.consume_codes(user_id, now)
        record = await self.verification_repo.create_code(
            user_id=user_id, phone=phone, code_hash=hash_secret(code), expires_at=now + SMS_CODE_TTL, now=now
        )
        await self.db.commit()

        try:
            await send_sms(phone, SMS_TEXTS[locale].format(code=code), idempotency_key=f"otp-{record.id}")
        except SmsError as error:
            # Код не ушёл — гасим, чтобы не ждать паузу перед повтором
            record.consumed_at = now
            await self.db.commit()
            if isinstance(error, SmsRejectedPhone):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Phone is rejected")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="SMS is unavailable")

        SMS_BY_USER.hit(user_key)
        SMS_BY_IP.hit(ip_key)
        return SmsSentOut(
            phone_hint=phone_hint, resend_after=SMS_RESEND_SECONDS, expires_in=int(SMS_CODE_TTL.total_seconds())
        )

    async def _consume_code(self, user_id: int, phone: str, code: str, client_ip: str | None) -> None:
        """
        Проверяет последний код пользователя, отправленный на phone, и гасит его.
        Неверный ввод считается; после SMS_CODE_ATTEMPTS код сгорает.
        """
        ip_key = client_ip or "unknown"
        if LOGIN_FAILURES_BY_IP.is_blocked(ip_key):
            raise _too_many_attempts()

        now = datetime.now(timezone.utc)
        record = await self.verification_repo.last_code(user_id, for_update=True)
        if not record or record.consumed_at is not None or record.expires_at <= now or record.phone != phone:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired")

        if not hmac.compare_digest(record.code_hash, hash_secret(code)):
            record.attempts += 1
            if record.attempts >= SMS_CODE_ATTEMPTS:
                record.consumed_at = now
            LOGIN_FAILURES_BY_IP.hit(ip_key)
            await self.db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

        record.consumed_at = now

    async def _methods(self, user: User) -> list[str]:
        """
        Чем можно подтвердить личность.

        - sms — телефон +992 (Payomchi доставляет только в Таджикистан)
        - google — уже привязанный Google; новый — только пока личность не подтверждена
          или подтвердить больше нечем: иначе укравший пароль подтвердил бы вход своим Google
        """
        methods = []
        if sms_enabled() and is_sms_phone(user.phone):
            methods.append("sms")
        if settings.GOOGLE_CLIENT_IDS and (
            user.verified_at is None
            or not methods
            or await self.repo.get_provider_user_id(user.id, GOOGLE_PROVIDER) is not None
        ):
            methods.append("google")
        return methods

    async def _challenge(self, user: User, purpose: str) -> ChallengeOut:
        methods = await self._methods(user)
        if not methods:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Verification is unavailable")
        return ChallengeOut(
            challenge=create_challenge_token(user_id=user.id, purpose=purpose),
            purpose=purpose,
            methods=methods,
            phone_hint=mask_phone(user.phone) if "sms" in methods else None,
        )

    async def _load_challenge(self, challenge: str, for_update: bool = False) -> tuple[User, str]:
        payload = decode_token(challenge, expected_type="challenge")
        user = await self.repo.get(int(payload["sub"]), for_update=for_update) if payload else None
        if not user or user.deleted_at is not None or payload.get("purpose") not in ("login", "password"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid challenge")
        return user, payload["purpose"]

    @staticmethod
    def _check_new_password(purpose: str, new_password: str | None) -> None:
        if purpose == "password" and not new_password:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="New password is required")

    async def _google_claims(self, id_token: str, ip_key: str) -> dict:
        if LOGIN_FAILURES_BY_IP.is_blocked(ip_key):
            raise _too_many_attempts()
        try:
            return await verify_google_id_token(id_token)
        except GoogleTokenError:
            LOGIN_FAILURES_BY_IP.hit(ip_key)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")
        except OSError:
            # Не скачались открытые ключи Google — проблема сети, а не токена
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google is unavailable")

    async def _complete_verification(
        self, user: User, purpose: str, new_password: str | None, user_agent: str | None
    ) -> AuthResult:
        """Личность подтверждена: отмечаем аккаунт и устройство, при смене пароля — меняем его, выдаём сессию."""
        now = datetime.now(timezone.utc)
        user.verified_at = user.verified_at or now
        if purpose == "password":
            user.hashed_password = hash_password(new_password)
            # Старый пароль мог утечь: выходим везде и забываем устройства
            await self.session_repo.revoke_all(user_id=user.id, now=now)
            await self.verification_repo.delete_devices(user.id)
            self.audit.add(
                fund_id=None, actor_id=user.id, action="user.password_change", entity="user", entity_id=user.id
            )

        device_token = generate_device_token()
        self.verification_repo.add_device(
            user_id=user.id,
            token_hash=hash_secret(device_token),
            user_agent=user_agent[:USER_AGENT_LENGTH] if user_agent else None,
            expires_at=now + TRUSTED_DEVICE_EXPIRE,
        )
        token, refresh_token = await self._start_session(user, user_agent)
        await self.db.commit()
        return AuthResult(token=token, refresh_token=refresh_token, device_token=device_token)

    async def _is_trusted_device(self, user_id: int, device_token: str | None) -> bool:
        if not device_token:
            return False
        device = await self.verification_repo.get_device(user_id, hash_secret(device_token))
        now = datetime.now(timezone.utc)
        if not device or device.expires_at <= now:
            return False
        device.last_used_at = now
        return True

    async def _start_session(self, user: User, user_agent: str | None) -> tuple[TokenOut, str]:
        session = await self.session_repo.create(
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE,
            user_agent=user_agent[:USER_AGENT_LENGTH] if user_agent else None,
        )
        return self._issue_tokens(user, session.id)

    async def _active_session(self, refresh_token: str | None):
        """(сессия, пользователь) по refresh-токену или (None, None), если сессия мертва."""
        payload = decode_token(refresh_token, expected_type="refresh") if refresh_token else None
        if not payload or not isinstance(payload.get("sid"), int):
            return None, None

        session = await self.session_repo.get(payload["sid"], for_update=True)
        if (
            not session
            or session.user_id != int(payload["sub"])
            or session.revoked_at is not None
            or session.expires_at <= datetime.now(timezone.utc)
        ):
            return None, None

        user = await self.repo.get(session.user_id)
        return (session, user) if user else (None, None)

    @staticmethod
    def _issue_tokens(user: User, session_id: int) -> tuple[TokenOut, str]:
        token = TokenOut(
            access_token=create_access_token(user_id=user.id, is_platform_admin=user.is_platform_admin),
            user=UserOut.model_validate(user),
        )
        return token, create_refresh_token(user_id=user.id, session_id=session_id)

    @staticmethod
    def _ensure_dev_mode() -> None:
        if not settings.DEV_MODE:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

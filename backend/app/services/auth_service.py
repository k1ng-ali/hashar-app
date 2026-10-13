from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import REFRESH_TOKEN_EXPIRE, settings
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.enums import FundRoleEnum, MemberStatusEnum
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.auth_session_repo import AuthSessionRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.plan_request_repo import PlanRequestRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import DeleteAccountIn, LoginIn, RegisterIn, TokenOut
from app.schemas.user import DemoMembershipOut, DemoUserOut, UserOut

# Неудачные входы: по логину — от перебора пароля одного человека,
# по IP — от перебора многих логинов с одного адреса
LOGIN_FAILURES_BY_LOGIN = SlidingWindowLimiter(limit=10, window_seconds=15 * 60)
LOGIN_FAILURES_BY_IP = SlidingWindowLimiter(limit=50, window_seconds=15 * 60)
REGISTRATIONS_BY_IP = SlidingWindowLimiter(limit=10, window_seconds=60 * 60)

# Длина User-Agent, которую сохраняем в сессии
USER_AGENT_LENGTH = 255

# Чем заменяются имя удалённого пользователя и его контакт в заявках на тариф
DELETED_USER_NAME = "Удалённый пользователь"
DELETED_CONTACT = "—"


def normalize_phone(phone: str | None) -> str | None:
    """«+7 (916) 123-45-67» → «+79161234567»."""
    if not phone:
        return None
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"+{digits}" if digits else None


def _too_many_attempts() -> HTTPException:
    return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts, try later")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db=db)
        self.member_repo = MemberRepository(db=db)
        self.session_repo = AuthSessionRepository(db=db)
        self.plan_request_repo = PlanRequestRepository(db=db)
        self.audit = AuditRepository(db=db)

    async def register(
        self,
        payload: RegisterIn,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[TokenOut, str]:
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
        result = await self._start_session(user, user_agent)
        await self.db.commit()
        return result

    async def login(
        self,
        payload: LoginIn,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[TokenOut, str]:
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
        result = await self._start_session(user, user_agent)
        await self.db.commit()
        return result

    async def refresh(self, refresh_token: str | None) -> tuple[TokenOut, str]:
        """Новый access-токен по живой сессии; срок сессии продлевается (скользящий)."""
        session, user = await self._active_session(refresh_token)
        if not session or not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

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
        """Выход на всех устройствах: украденный refresh-токен больше не сработает."""
        await self.session_repo.revoke_all(user_id=user_id, now=datetime.now(timezone.utc))
        await self.db.commit()

    async def me(self, user_id: int) -> UserOut:
        user = await self.repo.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
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

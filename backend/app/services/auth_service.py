from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.user import User
from app.repositories.member_repo import MemberRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginIn, RegisterIn, TokenOut
from app.schemas.user import DemoMembershipOut, DemoUserOut, UserOut


def normalize_phone(phone: str | None) -> str | None:
    """«+7 (916) 123-45-67» → «+79161234567»."""
    if not phone:
        return None
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"+{digits}" if digits else None


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db=db)
        self.member_repo = MemberRepository(db=db)

    async def register(self, payload: RegisterIn) -> tuple[TokenOut, str]:
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
        await self.db.commit()
        return self._issue_tokens(user)

    async def login(self, payload: LoginIn) -> tuple[TokenOut, str]:
        login = payload.login.strip()
        user = await self.repo.get_by_login(normalize_phone(login) if "@" not in login else login)
        if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login or password")
        return self._issue_tokens(user)

    async def refresh(self, refresh_token: str | None) -> tuple[TokenOut, str]:
        payload = decode_token(refresh_token, expected_type="refresh") if refresh_token else None
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = await self.repo.get(int(payload["sub"]))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return self._issue_tokens(user)

    async def me(self, user_id: int) -> UserOut:
        user = await self.repo.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserOut.model_validate(user)

    # ─── DEV_MODE ──────────────────────────────────────────────────────────────

    async def dev_login(self, user_id: int) -> tuple[TokenOut, str]:
        self._ensure_dev_mode()
        user = await self.repo.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return self._issue_tokens(user)

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
    def _issue_tokens(user: User) -> tuple[TokenOut, str]:
        token = TokenOut(
            access_token=create_access_token(user_id=user.id, is_platform_admin=user.is_platform_admin),
            user=UserOut.model_validate(user),
        )
        return token, create_refresh_token(user_id=user.id)

    @staticmethod
    def _ensure_dev_mode() -> None:
        if not settings.DEV_MODE:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

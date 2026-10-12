from datetime import datetime

from sqlalchemy import select, update

from app.models.auth_session import AuthSession
from app.repositories.base_repo import BaseRepository


class AuthSessionRepository(BaseRepository):

    async def get(self, session_id: int, for_update: bool = False) -> AuthSession | None:
        stmt = select(AuthSession).where(AuthSession.id == session_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: int, expires_at: datetime, user_agent: str | None) -> AuthSession:
        session = AuthSession(user_id=user_id, expires_at=expires_at, user_agent=user_agent)
        self.db.add(session)
        await self.db.flush()
        return session

    async def revoke_all(self, user_id: int, now: datetime) -> None:
        await self.db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )

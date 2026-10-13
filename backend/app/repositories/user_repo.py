from sqlalchemy import delete, or_, select

from app.models.user import User, UserAuthProvider
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository):

    async def get(self, user_id: int, for_update: bool = False) -> User | None:
        stmt = select(User).where(User.id == user_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_login(self, login: str) -> User | None:
        """Поиск по телефону или email (без учёта регистра для email)."""
        result = await self.db.execute(
            select(User).where(or_(User.phone == login, User.email == login.lower())).limit(1)
        )
        return result.scalar_one_or_none()

    async def exists_login(self, phone: str | None, email: str | None) -> bool:
        conditions = []
        if phone:
            conditions.append(User.phone == phone)
        if email:
            conditions.append(User.email == email)
        if not conditions:
            return False
        result = await self.db.execute(select(User.id).where(or_(*conditions)).limit(1))
        return result.scalar_one_or_none() is not None

    async def list_all(self) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.deleted_at.is_(None)).order_by(User.is_platform_admin.desc(), User.id)
        )
        return list(result.scalars().all())

    async def create(
        self,
        full_name: str,
        phone: str | None,
        email: str | None,
        hashed_password: str | None,
    ) -> User:
        user = User(full_name=full_name, phone=phone, email=email, hashed_password=hashed_password)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete_auth_providers(self, user_id: int) -> None:
        await self.db.execute(delete(UserAuthProvider).where(UserAuthProvider.user_id == user_id))

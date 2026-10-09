from sqlalchemy import or_, select

from app.models.user import User
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository):

    async def get(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
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
        result = await self.db.execute(select(User).order_by(User.is_platform_admin.desc(), User.id))
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

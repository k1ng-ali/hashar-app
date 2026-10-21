# Метод list() в классе затеняет встроенный list в аннотациях ниже (Python 3.12) — аннотации отложенные
from __future__ import annotations

from sqlalchemy import case, func, select
from sqlalchemy.orm import selectinload

from app.enums import FundRoleEnum, MemberStatusEnum
from app.models.member import FundMember
from app.repositories.base_repo import BaseRepository

ACTIVE = MemberStatusEnum.active.value


class MemberRepository(BaseRepository):

    async def get(self, fund_id: int, member_id: int, for_update: bool = False) -> FundMember | None:
        stmt = (
            select(FundMember)
            .where(FundMember.id == member_id, FundMember.fund_id == fund_id)
            .options(selectinload(FundMember.user))
            .execution_options(populate_existing=True)
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user(self, fund_id: int, user_id: int) -> FundMember | None:
        result = await self.db.execute(
            select(FundMember).where(FundMember.fund_id == fund_id, FundMember.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_chairman(self, fund_id: int) -> FundMember | None:
        result = await self.db.execute(
            select(FundMember).where(
                FundMember.fund_id == fund_id,
                FundMember.role == FundRoleEnum.chairman.value,
            )
        )
        return result.scalar_one_or_none()

    async def list(self, fund_id: int, status: str | None = None) -> list[FundMember]:
        # Председатель, совет, затем жители по помещению
        role_order = case({"chairman": 0, "admin": 1}, value=FundMember.role, else_=2)
        stmt = select(FundMember).where(FundMember.fund_id == fund_id).options(selectinload(FundMember.user))
        if status:
            stmt = stmt.where(FundMember.status == status)
        result = await self.db.execute(stmt.order_by(role_order, FundMember.address_unit, FundMember.id))
        return list(result.scalars().all())

    async def list_council_by_funds(self, fund_ids: list[int]) -> dict[int, list[FundMember]]:
        """{fund_id: [председатель, администраторы]} — активные члены совета с пользователями."""
        if not fund_ids:
            return {}
        role_order = case({"chairman": 0}, value=FundMember.role, else_=1)
        result = await self.db.execute(
            select(FundMember)
            .where(
                FundMember.fund_id.in_(fund_ids),
                FundMember.status == ACTIVE,
                FundMember.role.in_([FundRoleEnum.chairman.value, FundRoleEnum.admin.value]),
            )
            .options(selectinload(FundMember.user))
            .order_by(FundMember.fund_id, role_order, FundMember.id)
        )
        council: dict[int, list[FundMember]] = {}
        for member in result.scalars().all():
            council.setdefault(member.fund_id, []).append(member)
        return council

    async def list_by_user(self, user_id: int) -> list[FundMember]:
        result = await self.db.execute(
            select(FundMember)
            .where(FundMember.user_id == user_id)
            .options(selectinload(FundMember.fund))
            .order_by(FundMember.created_at)
        )
        return list(result.scalars().all())

    async def first_council_user_ids(self, fund_id: int, limit: int) -> list[int]:
        """Первые limit членов совета: председатель, затем администраторы по давности членства."""
        role_order = case({"chairman": 0}, value=FundMember.role, else_=1)
        result = await self.db.execute(
            select(FundMember.user_id)
            .where(
                FundMember.fund_id == fund_id,
                FundMember.status == ACTIVE,
                FundMember.role.in_([FundRoleEnum.chairman.value, FundRoleEnum.admin.value]),
            )
            .order_by(role_order, FundMember.id)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_active(self, fund_id: int) -> int:
        result = await self.db.execute(
            select(func.count(FundMember.id)).where(FundMember.fund_id == fund_id, FundMember.status == ACTIVE)
        )
        return result.scalar() or 0

    async def count_active_by_funds(self, fund_ids: list[int]) -> dict[int, int]:
        if not fund_ids:
            return {}
        result = await self.db.execute(
            select(FundMember.fund_id, func.count(FundMember.id))
            .where(FundMember.fund_id.in_(fund_ids), FundMember.status == ACTIVE)
            .group_by(FundMember.fund_id)
        )
        return {fund_id: int(count) for fund_id, count in result.all()}

    async def has_other_council(self, fund_id: int, user_id: int) -> bool:
        """Есть ли в совете фонда кто-то ещё, кроме этого пользователя."""
        result = await self.db.execute(
            select(FundMember.id)
            .where(
                FundMember.fund_id == fund_id,
                FundMember.user_id != user_id,
                FundMember.status == ACTIVE,
                FundMember.role.in_([FundRoleEnum.chairman.value, FundRoleEnum.admin.value]),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def count_by_status(self, fund_id: int, status: str) -> int:
        result = await self.db.execute(
            select(func.count(FundMember.id)).where(FundMember.fund_id == fund_id, FundMember.status == status)
        )
        return result.scalar() or 0

    async def units_by_users(self, fund_id: int, user_ids: list[int]) -> dict[int, tuple[str | None, str]]:
        """{user_id: (помещение, роль)} — для подписей авторов."""
        if not user_ids:
            return {}
        result = await self.db.execute(
            select(FundMember.user_id, FundMember.address_unit, FundMember.role).where(
                FundMember.fund_id == fund_id, FundMember.user_id.in_(user_ids)
            )
        )
        return {user_id: (unit, role) for user_id, unit, role in result.all()}

    async def create(self, **fields) -> FundMember:
        member = FundMember(**fields)
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

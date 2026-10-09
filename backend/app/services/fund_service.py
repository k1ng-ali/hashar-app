from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.codes import generate_fund_code
from app.core.finance import current_period
from app.enums import FundRoleEnum, MemberStatusEnum
from app.models.fund import Fund
from app.repositories.fund_repo import FundRepository
from app.repositories.member_repo import MemberRepository
from app.schemas.fund import FundCreateIn, FundOut, FundPublicOut, FundUpdateIn, MyFundOut
from app.schemas.member import FundContext, JoinIn, MemberOut
from app.services.account_service import AccountService
from app.services.member_service import member_out
from app.services.plan_service import PlanService

# Попыток подобрать свободный код фонда
CODE_ATTEMPTS = 10


class FundService:
    """Фонды платформы: создание, поиск, вступление, карточка и настройки фонда."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = FundRepository(db=db)
        self.member_repo = MemberRepository(db=db)
        self.accounts = AccountService(db=db)
        self.plans = PlanService(db=db)

    # ─── Создание ──────────────────────────────────────────────────────────────

    async def create(self, user_id: int, payload: FundCreateIn) -> FundOut:
        fund = await self.repo.create(
            name=payload.name.strip(),
            description=payload.description,
            address=payload.address,
            code=await self._free_code(),
            base_currency=payload.base_currency.value,
            monthly_rate=payload.monthly_rate,
            start_period=payload.start_period or current_period(),
            created_by_id=user_id,
        )

        # Счёт базовой валюты есть всегда, остальные — по выбору председателя
        currencies = [payload.base_currency.value] + [c.value for c in payload.currencies if c != payload.base_currency]
        for currency in dict.fromkeys(currencies):
            await self.repo.create_account(fund.id, currency)

        # Создатель — председатель фонда (фонд не существует без председателя)
        await self.member_repo.create(
            fund_id=fund.id,
            user_id=user_id,
            role=FundRoleEnum.chairman.value,
            status=MemberStatusEnum.active.value,
            address_unit=payload.address_unit,
            joined_at=datetime.now(timezone.utc),
        )
        await self.db.commit()
        return await self._fund_out(fund, FundRoleEnum.chairman)

    # ─── Поиск и вступление ────────────────────────────────────────────────────

    async def search(self, user_id: int, query: str) -> list[FundPublicOut]:
        query = query.strip()
        if len(query) < 2:
            return []
        return await self._public_many(await self.repo.search(query), user_id)

    async def get_by_code(self, user_id: int, code: str) -> FundPublicOut:
        fund = await self.repo.get_by_code(code.strip())
        if not fund:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fund not found")
        return (await self._public_many([fund], user_id))[0]

    async def join(self, fund_id: int, user_id: int, payload: JoinIn) -> MemberOut:
        """Заявка на вступление. Фонд станет доступен после одобрения советом."""
        fund = await self.repo.get(fund_id)
        if not fund:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fund not found")

        member = await self.member_repo.get_by_user(fund_id, user_id)
        if member:
            if member.status == MemberStatusEnum.active.value:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member")
            if member.status == MemberStatusEnum.pending.value:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request is already pending")
            if member.status == MemberStatusEnum.blocked.value:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Blocked in this fund")
            # Отклонённую заявку можно подать повторно
            member.status = MemberStatusEnum.pending.value
            member.address_unit = payload.address_unit.strip()
            member.message = payload.message
            member.role = FundRoleEnum.resident.value
        else:
            member = await self.member_repo.create(
                fund_id=fund_id,
                user_id=user_id,
                address_unit=payload.address_unit.strip(),
                message=payload.message,
            )
        await self.db.commit()
        return member_out(await self.member_repo.get(fund_id, member.id))

    async def cancel_request(self, fund_id: int, user_id: int) -> None:
        member = await self.member_repo.get_by_user(fund_id, user_id)
        if not member or member.status != MemberStatusEnum.pending.value:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        await self.db.delete(member)
        await self.db.commit()

    async def leave(self, ctx: FundContext) -> None:
        if ctx.is_chairman:
            # Фонд не существует без председателя — сначала передайте права
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Transfer chairman rights first")
        member = await self.member_repo.get(ctx.fund_id, ctx.member_id)
        await self.db.delete(member)
        await self.db.commit()

    # ─── Мои фонды и карточка ──────────────────────────────────────────────────

    async def list_my(self, user_id: int) -> list[MyFundOut]:
        memberships = await self.member_repo.list_by_user(user_id)
        return [
            MyFundOut(
                id=m.fund.id,
                name=m.fund.name,
                address=m.fund.address,
                code=m.fund.code,
                base_currency=m.fund.base_currency,
                role=m.role,
                status=m.status,
                address_unit=m.address_unit,
            )
            # Показываем все статусы: пользователь видит и заявки, и отказы
            for m in memberships
        ]

    async def get(self, ctx: FundContext) -> FundOut:
        return await self._fund_out(await self._get_or_404(ctx.fund_id), ctx.role)

    async def update(self, ctx: FundContext, payload: FundUpdateIn) -> FundOut:
        fund = await self._get_or_404(ctx.fund_id, for_update=True)
        data = payload.model_dump(exclude_none=True)

        # Финансовые настройки меняет только председатель
        financial = {"base_currency", "monthly_rate", "start_period"}
        if financial & data.keys() and not ctx.is_chairman:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the chairman can do this")

        if "base_currency" in data:
            await self.accounts.ensure_active_currency(fund.id, payload.base_currency.value)
            data["base_currency"] = payload.base_currency.value

        for field, value in data.items():
            setattr(fund, field, value)
        await self.db.commit()
        return await self._fund_out(fund, ctx.role)

    # ─── Helpers ───────────────────────────────────────────────────────────────

    async def _fund_out(self, fund: Fund, role: FundRoleEnum) -> FundOut:
        return FundOut(
            id=fund.id,
            name=fund.name,
            description=fund.description,
            address=fund.address,
            code=fund.code,
            base_currency=fund.base_currency,
            monthly_rate=fund.monthly_rate,
            start_period=fund.start_period,
            accounts=await self.accounts.list_accounts(fund.id),
            plan=await self.plans.info(fund),
            my_role=role,
            created_at=fund.created_at,
        )

    async def _public_many(self, funds: list[Fund], user_id: int) -> list[FundPublicOut]:
        counts = await self.member_repo.count_active_by_funds([f.id for f in funds])
        result = []
        for fund in funds:
            member = await self.member_repo.get_by_user(fund.id, user_id)
            result.append(
                FundPublicOut(
                    id=fund.id,
                    name=fund.name,
                    address=fund.address,
                    code=fund.code,
                    members_count=counts.get(fund.id, 0),
                    my_status=member.status if member else None,
                )
            )
        return result

    async def _free_code(self) -> str:
        for _ in range(CODE_ATTEMPTS):
            code = generate_fund_code()
            if not await self.repo.code_exists(code):
                return code
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate fund code")

    async def _get_or_404(self, fund_id: int, for_update: bool = False) -> Fund:
        fund = await self.repo.get(fund_id, for_update=for_update)
        if not fund:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fund not found")
        return fund

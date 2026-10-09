from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.finance import current_period
from app.enums import ContributionCategoryEnum, ContributionStatusEnum
from app.models.contribution import Contribution
from app.repositories.contribution_repo import ContributionRepository
from app.repositories.fund_repo import FundRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.target_fund_repo import TargetFundRepository
from app.schemas.contribution import ContributionCreateIn, ContributionOut
from app.services.account_service import AccountService


def contribution_out(contribution: Contribution) -> ContributionOut:
    """ORM → схема с подтянутыми именами участника, сбора и проверяющего."""
    return ContributionOut(
        id=contribution.id,
        user_id=contribution.user_id,
        user_name=contribution.user.full_name,
        user_unit=contribution.user_unit,
        amount=contribution.amount,
        currency=contribution.currency,
        category=contribution.category,
        target_fund_id=contribution.target_fund_id,
        target_fund_title=contribution.target_fund.title if contribution.target_fund else None,
        billing_period=contribution.billing_period,
        receipt_image=contribution.receipt_image,
        status=contribution.status,
        comment_user=contribution.comment_user,
        comment_admin=contribution.comment_admin,
        reviewed_by_name=contribution.reviewed_by.full_name if contribution.reviewed_by else None,
        reviewed_at=contribution.reviewed_at,
        created_at=contribution.created_at,
    )


class ContributionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ContributionRepository(db=db)
        self.fund_repo = FundRepository(db=db)
        self.member_repo = MemberRepository(db=db)
        self.target_fund_repo = TargetFundRepository(db=db)
        self.accounts = AccountService(db=db)

    # ─── Участник ──────────────────────────────────────────────────────────────

    async def list_my(
        self,
        fund_id: int,
        user_id: int,
        status_filter: ContributionStatusEnum | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ContributionOut]:
        items = await self.repo.list(
            fund_id,
            user_id=user_id,
            status=status_filter.value if status_filter else None,
            skip=skip,
            limit=limit,
        )
        return [contribution_out(item) for item in items]

    async def create(self, fund_id: int, user_id: int, payload: ContributionCreateIn) -> ContributionOut:
        # Валюта взноса = валюта реквизита, на который перевели деньги
        requisite = await self.accounts.get_active_requisite(fund_id, payload.requisite_id)
        fund = await self.fund_repo.get(fund_id)

        target_fund_id = None
        billing_period = None
        if payload.category == ContributionCategoryEnum.target_fund:
            target_fund = await self.target_fund_repo.get(fund_id, payload.target_fund_id)
            if not target_fund:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target fund not found")
            if not target_fund.is_active:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target fund is closed")
            if target_fund.currency != requisite.currency:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Currency must match the target fund")
            target_fund_id = target_fund.id
        else:
            # Ежемесячный тариф и долги считаются только в базовой валюте фонда
            if requisite.currency != fund.base_currency:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Monthly fee must be in base currency")
            billing_period = payload.billing_period or current_period()

        member = await self.member_repo.get_by_user(fund_id, user_id)
        contribution = await self.repo.create(
            fund_id=fund_id,
            user_id=user_id,
            user_unit=member.address_unit if member else None,
            amount=payload.amount,
            currency=requisite.currency,
            requisite_id=requisite.id,
            category=payload.category.value,
            target_fund_id=target_fund_id,
            billing_period=billing_period,
            receipt_image=payload.receipt_image,
            comment_user=payload.comment_user,
        )
        await self.db.commit()
        return contribution_out(contribution)

    # ─── Совет фонда ───────────────────────────────────────────────────────────

    async def list_all(
        self,
        fund_id: int,
        status_filter: ContributionStatusEnum | None = None,
        category: ContributionCategoryEnum | None = None,
        user_id: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ContributionOut]:
        items = await self.repo.list(
            fund_id,
            user_id=user_id,
            status=status_filter.value if status_filter else None,
            category=category.value if category else None,
            skip=skip,
            limit=limit,
        )
        return [contribution_out(item) for item in items]

    async def approve(
        self,
        fund_id: int,
        contribution_id: int,
        reviewer_id: int,
        comment: str | None = None,
    ) -> ContributionOut:
        return await self._review(fund_id, contribution_id, reviewer_id, ContributionStatusEnum.approved, comment)

    async def reject(self, fund_id: int, contribution_id: int, reviewer_id: int, reason: str) -> ContributionOut:
        return await self._review(fund_id, contribution_id, reviewer_id, ContributionStatusEnum.rejected, reason)

    async def _review(
        self,
        fund_id: int,
        contribution_id: int,
        reviewer_id: int,
        new_status: ContributionStatusEnum,
        comment: str | None,
    ) -> ContributionOut:
        # Блокируем строку: два члена совета не должны проверить один чек одновременно
        contribution = await self.repo.get(fund_id, contribution_id, for_update=True)
        if not contribution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contribution not found")
        if contribution.status != ContributionStatusEnum.pending.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contribution already reviewed")

        contribution.status = new_status.value
        contribution.comment_admin = comment
        contribution.reviewed_by_id = reviewer_id
        contribution.reviewed_at = datetime.now(timezone.utc)
        await self.db.commit()

        return contribution_out(await self.repo.get(fund_id, contribution_id))

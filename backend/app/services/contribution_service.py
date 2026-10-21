from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.finance import current_period
from app.core.receipts import receipt_url, store_receipt
from app.enums import ContributionCategoryEnum, ContributionStatusEnum, FundRoleEnum
from app.models.contribution import Contribution
from app.repositories.audit_repo import AuditRepository
from app.repositories.contribution_repo import ContributionFilters, ContributionRepository
from app.repositories.fund_repo import FundRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.target_fund_repo import TargetFundRepository
from app.schemas.contribution import (
    ContributionCreateIn,
    ContributionHistoryOut,
    ContributionOut,
    CurrencyTotalOut,
)
from app.services.account_service import AccountService, requisite_label
from app.services.plan_service import PlanService


def contribution_out(contribution: Contribution, show_receipt: bool = True) -> ContributionOut:
    """ORM → схема с подтянутыми именами участника, сбора и проверяющего. show_receipt=False — без чека."""
    return ContributionOut(
        id=contribution.id,
        user_id=contribution.user_id,
        user_name=contribution.user.full_name,
        user_unit=contribution.user_unit,
        amount=contribution.amount,
        currency=contribution.currency,
        credited_amount=contribution.credited_amount,
        credited_currency=contribution.credited_currency,
        requisite_id=contribution.requisite_id,
        requisite_label=contribution.requisite_label,
        category=contribution.category,
        target_fund_id=contribution.target_fund_id,
        target_fund_title=contribution.target_fund.title if contribution.target_fund else None,
        billing_period=contribution.billing_period,
        receipt_image=receipt_url(contribution.receipt_image) if show_receipt else None,
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
        self.audit = AuditRepository(db=db)
        self.accounts = AccountService(db=db)
        self.plans = PlanService(db=db)

    # ─── Участник ──────────────────────────────────────────────────────────────

    async def list_my(
        self,
        fund_id: int,
        user_id: int,
        status_filter: ContributionStatusEnum | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ContributionOut]:
        filters = ContributionFilters(user_id=user_id, status=status_filter.value if status_filter else None)
        items = await self.repo.list(fund_id, filters, skip=skip, limit=limit)
        return [contribution_out(item) for item in items]

    async def create(self, fund_id: int, user_id: int, payload: ContributionCreateIn) -> ContributionOut:
        # Валюта взноса = валюта реквизита, на который перевели деньги
        requisite = await self.accounts.get_active_requisite(fund_id, payload.requisite_id)
        fund = await self.fund_repo.get(fund_id)
        member = await self.member_repo.get_by_user(fund_id, user_id)
        # Тариф не продлён после льготного срока — вносят только 10 членов совета
        await self.plans.ensure_can_contribute(fund, user_id, FundRoleEnum(member.role) if member else None)

        target_fund_id = None
        billing_period = None
        if payload.category == ContributionCategoryEnum.target_fund:
            target_fund = await self.target_fund_repo.get(fund_id, payload.target_fund_id)
            if not target_fund:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target fund not found")
            if not target_fund.is_active:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target fund is closed")
            target_fund_id = target_fund.id
            credited_currency = target_fund.currency
        else:
            billing_period = payload.billing_period or current_period()
            # Ежемесячный тариф и долги считаются только в базовой валюте фонда
            credited_currency = fund.base_currency

        # Оплата в другой валюте: сколько зачесть, указывает сам участник — курс платформа не считает
        if requisite.currency == credited_currency:
            credited_amount = payload.amount
        elif payload.credited_amount:
            credited_amount = payload.credited_amount
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="credited_amount is required when paying in another currency",
            )

        contribution = await self.repo.create(
            fund_id=fund_id,
            user_id=user_id,
            user_unit=member.address_unit if member else None,
            amount=payload.amount,
            currency=requisite.currency,
            credited_amount=credited_amount,
            credited_currency=credited_currency,
            requisite_id=requisite.id,
            requisite_label=requisite_label(requisite),
            category=payload.category.value,
            target_fund_id=target_fund_id,
            billing_period=billing_period,
            receipt_image=await store_receipt(payload.receipt_image, fund_id, user_id),
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
        filters = ContributionFilters(
            user_id=user_id,
            status=status_filter.value if status_filter else None,
            category=category.value if category else None,
        )
        items = await self.repo.list(fund_id, filters, skip=skip, limit=limit)
        return [contribution_out(item) for item in items]

    async def history(
        self,
        fund_id: int,
        filters: ContributionFilters,
        skip: int = 0,
        limit: int = 30,
    ) -> ContributionHistoryOut:
        """История чеков для совета: фильтры по статусу, реквизиту, валюте и участнику + итоги."""
        if filters.search:
            filters.search = filters.search.strip() or None
        totals = await self.repo.totals(fund_id, filters)
        items = await self.repo.list(fund_id, filters, skip=skip, limit=limit)
        return ContributionHistoryOut(
            items=[contribution_out(item) for item in items],
            total_count=sum(count for _, _, count in totals),
            totals=[
                CurrencyTotalOut(currency=currency, amount=amount, count=count) for currency, amount, count in totals
            ],
        )

    async def approve(
        self,
        fund_id: int,
        contribution_id: int,
        reviewer_id: int,
        comment: str | None = None,
        credited_amount: int | None = None,
    ) -> ContributionOut:
        return await self._review(
            fund_id, contribution_id, reviewer_id, ContributionStatusEnum.approved, comment, credited_amount
        )

    async def reject(self, fund_id: int, contribution_id: int, reviewer_id: int, reason: str) -> ContributionOut:
        return await self._review(fund_id, contribution_id, reviewer_id, ContributionStatusEnum.rejected, reason)

    async def _review(
        self,
        fund_id: int,
        contribution_id: int,
        reviewer_id: int,
        new_status: ContributionStatusEnum,
        comment: str | None,
        credited_amount: int | None = None,
    ) -> ContributionOut:
        # Блокируем строку: два члена совета не должны проверить один чек одновременно
        contribution = await self.repo.get(fund_id, contribution_id, for_update=True)
        if not contribution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contribution not found")
        if contribution.status != ContributionStatusEnum.pending.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contribution already reviewed")
        # Свой чек одобряет другой член совета. Исключение — совет из одного человека,
        # иначе его взносы не одобрил бы никто
        if (
            new_status == ContributionStatusEnum.approved
            and contribution.user_id == reviewer_id
            and await self.member_repo.has_other_council(fund_id, reviewer_id)
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot approve your own contribution")

        contribution.status = new_status.value
        # Поправка зачтённой суммы имеет смысл только для оплаты в другой валюте
        if credited_amount and contribution.currency != contribution.credited_currency:
            contribution.credited_amount = credited_amount
        contribution.comment_admin = comment
        contribution.reviewed_by_id = reviewer_id
        contribution.reviewed_at = datetime.now(timezone.utc)
        self.audit.add(
            fund_id=fund_id,
            actor_id=reviewer_id,
            action=f"contribution.{new_status.value}",
            entity="contribution",
            entity_id=contribution.id,
            details={
                "user_id": contribution.user_id,
                "amount": contribution.amount,
                "currency": contribution.currency,
                "credited_amount": contribution.credited_amount,
                "credited_currency": contribution.credited_currency,
                "comment": comment,
            },
        )
        await self.db.commit()

        return contribution_out(await self.repo.get(fund_id, contribution_id))

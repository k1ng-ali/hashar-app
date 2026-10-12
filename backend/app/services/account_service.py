from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import AnnouncementCategoryEnum, CurrencyEnum
from app.models.requisite import PaymentRequisite
from app.models.transfer import AccountTransfer
from app.repositories.announcement_repo import AnnouncementRepository
from app.repositories.contribution_repo import ContributionRepository
from app.repositories.expense_repo import ExpenseRepository
from app.repositories.fund_repo import FundRepository
from app.repositories.requisite_repo import RequisiteRepository
from app.repositories.transfer_repo import TransferRepository
from app.schemas.account import RequisiteCreateIn, RequisiteOut, TransferCreateIn, TransferOut
from app.schemas.fund import AccountOut

# Заголовок автоматического объявления; на фронте подменяется переводом по transfer
TRANSFER_ANNOUNCEMENT_TITLE = "Движение по счетам фонда"


def transfer_out(transfer: AccountTransfer) -> TransferOut:
    return TransferOut(
        id=transfer.id,
        from_currency=transfer.from_currency,
        from_amount=transfer.from_amount,
        to_currency=transfer.to_currency,
        to_amount=transfer.to_amount,
        comment=transfer.comment,
        created_by_name=transfer.created_by.full_name if transfer.created_by else None,
        created_at=transfer.created_at,
    )


class AccountService:
    """Валютные счета фонда, реквизиты для оплаты и переводы между счетами."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fund_repo = FundRepository(db=db)
        self.requisite_repo = RequisiteRepository(db=db)
        self.transfer_repo = TransferRepository(db=db)
        self.contribution_repo = ContributionRepository(db=db)
        self.expense_repo = ExpenseRepository(db=db)
        self.announcement_repo = AnnouncementRepository(db=db)

    # ─── Балансы ───────────────────────────────────────────────────────────────

    async def ensure_sufficient(self, fund_id: int, currency: str, amount: int, allow_overdraft: bool) -> None:
        """
        409, если списание уводит счёт в минус и это не подтверждено явно.

        Минус не запрещён совсем: платформа — учёт, а не банк. Расход мог быть оплачен
        из личных средств председателя или в долг подрядчику, а взносы — ещё не внесены
        в систему. Но такое действие должно быть осознанным, а не опечаткой.
        Строку фонда блокируем, чтобы два параллельных расхода не прошли проверку оба.
        """
        await self.fund_repo.get(fund_id, for_update=True)
        if allow_overdraft:
            return
        balance = (await self.balances(fund_id)).get(currency, 0)
        if amount > balance:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient funds")

    async def balances(
        self,
        fund_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict[str, int]:
        """Остаток по каждой валюте = взносы − расходы + зачисления − списания."""
        income = await self.contribution_repo.approved_sums_by_currency(fund_id, start=start, end=end)
        spent = await self.expense_repo.sums_by_currency(fund_id, start=start, end=end)
        transfers_in, transfers_out = await self.transfer_repo.sums_by_currency(fund_id, start=start, end=end)

        return {
            currency.value: income.get(currency.value, 0)
            - spent.get(currency.value, 0)
            + transfers_in.get(currency.value, 0)
            - transfers_out.get(currency.value, 0)
            for currency in CurrencyEnum
        }

    async def list_accounts(self, fund_id: int, active_only: bool = False) -> list[AccountOut]:
        accounts = await self.fund_repo.list_accounts(fund_id, active_only=active_only)
        balances = await self.balances(fund_id)
        return [AccountOut(currency=a.currency, is_active=a.is_active, balance=balances[a.currency]) for a in accounts]

    async def active_currencies(self, fund_id: int) -> list[str]:
        return [a.currency for a in await self.fund_repo.list_accounts(fund_id, active_only=True)]

    async def ensure_active_currency(self, fund_id: int, currency: str) -> None:
        if currency not in await self.active_currencies(fund_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Currency account is not enabled")

    # ─── Управление счетами ────────────────────────────────────────────────────

    async def enable_currency(self, fund_id: int, currency: CurrencyEnum) -> list[AccountOut]:
        account = await self.fund_repo.get_account(fund_id, currency.value)
        if account:
            account.is_active = True
        else:
            await self.fund_repo.create_account(fund_id, currency.value)
        await self.db.commit()
        return await self.list_accounts(fund_id)

    async def disable_currency(self, fund_id: int, currency: CurrencyEnum) -> list[AccountOut]:
        fund = await self.fund_repo.get(fund_id)
        if fund.base_currency == currency.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot disable the base currency")

        account = await self.fund_repo.get_account(fund_id, currency.value)
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        # Деньги не должны «потеряться»: сначала переведите остаток на другой счёт
        if (await self.balances(fund_id))[currency.value] != 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account balance must be zero")

        account.is_active = False
        await self.db.commit()
        return await self.list_accounts(fund_id)

    # ─── Реквизиты ─────────────────────────────────────────────────────────────

    async def list_requisites(self, fund_id: int, active_only: bool = False) -> list[RequisiteOut]:
        # Участникам показываем реквизиты только включённых валют
        currencies = await self.active_currencies(fund_id) if active_only else None
        items = await self.requisite_repo.list(fund_id, active_only=active_only, currencies=currencies)
        return [RequisiteOut.model_validate(item) for item in items]

    async def create_requisite(self, fund_id: int, payload: RequisiteCreateIn) -> RequisiteOut:
        await self.ensure_active_currency(fund_id, payload.currency.value)
        data = payload.model_dump()
        data["currency"] = payload.currency.value
        requisite = await self.requisite_repo.create(fund_id=fund_id, **data)
        await self.db.commit()
        return RequisiteOut.model_validate(requisite)

    async def toggle_requisite(self, fund_id: int, requisite_id: int) -> RequisiteOut:
        requisite = await self._get_requisite_or_404(fund_id, requisite_id)
        requisite.is_active = not requisite.is_active
        await self.db.commit()
        return RequisiteOut.model_validate(requisite)

    async def delete_requisite(self, fund_id: int, requisite_id: int) -> None:
        requisite = await self._get_requisite_or_404(fund_id, requisite_id)
        await self.requisite_repo.delete(requisite)
        await self.db.commit()

    async def get_active_requisite(self, fund_id: int, requisite_id: int) -> PaymentRequisite:
        requisite = await self.requisite_repo.get(fund_id, requisite_id)
        if not requisite or not requisite.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisite not found")
        await self.ensure_active_currency(fund_id, requisite.currency)
        return requisite

    # ─── Переводы ──────────────────────────────────────────────────────────────

    async def list_transfers(self, fund_id: int, skip: int = 0, limit: int = 50) -> list[TransferOut]:
        return [transfer_out(t) for t in await self.transfer_repo.list(fund_id, skip=skip, limit=limit)]

    async def create_transfer(self, fund_id: int, user_id: int, payload: TransferCreateIn) -> TransferOut:
        active = await self.active_currencies(fund_id)
        for currency in (payload.from_currency, payload.to_currency):
            if currency is not None and currency.value not in active:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Currency account is not enabled")
        if payload.from_currency is not None:
            await self.ensure_sufficient(
                fund_id, payload.from_currency.value, payload.from_amount, payload.allow_overdraft
            )

        transfer = await self.transfer_repo.create(
            fund_id=fund_id,
            from_currency=payload.from_currency.value if payload.from_currency else None,
            from_amount=payload.from_amount,
            to_currency=payload.to_currency.value if payload.to_currency else None,
            to_amount=payload.to_amount,
            comment=payload.comment.strip(),
            created_by_id=user_id,
        )
        # Прозрачность: каждое движение по счетам публикуется на доске объявлений
        await self.announcement_repo.create(
            fund_id=fund_id,
            title=TRANSFER_ANNOUNCEMENT_TITLE,
            content=transfer.comment,
            category=AnnouncementCategoryEnum.finance.value,
            author_id=user_id,
            transfer_id=transfer.id,
        )
        await self.db.commit()
        return transfer_out(transfer)

    # ─── Helpers ───────────────────────────────────────────────────────────────

    async def _get_requisite_or_404(self, fund_id: int, requisite_id: int) -> PaymentRequisite:
        requisite = await self.requisite_repo.get(fund_id, requisite_id)
        if not requisite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisite not found")
        return requisite

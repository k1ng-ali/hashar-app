from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.enums import CurrencyEnum, ExpenseCategoryEnum
from app.schemas.account import TransferCreateIn
from app.schemas.expense import ExpenseCreateIn
from app.services.account_service import AccountService
from app.services.expense_service import ExpenseService
from tests.unit.helpers import make_db, make_fund


def make_expense_service(balance: int):
    db = make_db()
    service = ExpenseService(db=db)
    service.accounts.ensure_active_currency = AsyncMock()
    service.accounts.fund_repo.get = AsyncMock(return_value=make_fund())
    service.accounts.balances = AsyncMock(return_value={"tjs": balance})
    service.repo.create = AsyncMock()
    return db, service


def expense_payload(amount: int, allow_overdraft: bool = False) -> ExpenseCreateIn:
    return ExpenseCreateIn(
        title="Ремонт",
        category=ExpenseCategoryEnum.repair,
        amount=amount,
        currency=CurrencyEnum.tjs,
        description="Замена замка",
        allow_overdraft=allow_overdraft,
    )


async def test_expense_over_balance_is_rejected():
    db, service = make_expense_service(balance=500)

    with pytest.raises(HTTPException) as exc:
        await service.create(fund_id=1, user_id=1, payload=expense_payload(600))

    assert exc.value.status_code == 409
    assert exc.value.detail == "Insufficient funds"
    db.commit.assert_not_called()


async def test_expense_over_balance_with_confirmation(monkeypatch):
    db, service = make_expense_service(balance=500)
    monkeypatch.setattr("app.services.expense_service.expense_out", lambda expense: expense)

    await service.create(fund_id=1, user_id=1, payload=expense_payload(600, allow_overdraft=True))

    service.repo.create.assert_awaited_once()
    db.commit.assert_awaited_once()


async def test_expense_within_balance_locks_fund_row(monkeypatch):
    db, service = make_expense_service(balance=500)
    monkeypatch.setattr("app.services.expense_service.expense_out", lambda expense: expense)

    await service.create(fund_id=1, user_id=1, payload=expense_payload(500))

    service.accounts.fund_repo.get.assert_awaited_once_with(1, for_update=True)
    db.commit.assert_awaited_once()


async def test_transfer_over_balance_is_rejected():
    service = AccountService(db=make_db())
    service.active_currencies = AsyncMock(return_value=["tjs", "rub"])
    service.fund_repo.get = AsyncMock(return_value=make_fund())
    service.balances = AsyncMock(return_value={"tjs": 100, "rub": 0})

    payload = TransferCreateIn(
        from_currency=CurrencyEnum.tjs, from_amount=200, to_currency=CurrencyEnum.rub, to_amount=1700, comment="Обмен"
    )
    with pytest.raises(HTTPException) as exc:
        await service.create_transfer(fund_id=1, user_id=1, payload=payload)

    assert exc.value.status_code == 409

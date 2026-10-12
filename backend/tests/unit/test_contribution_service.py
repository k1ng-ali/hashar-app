from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.enums import ContributionCategoryEnum
from app.schemas.contribution import ContributionCreateIn
from app.services.contribution_service import ContributionService
from tests.unit.helpers import make_contribution, make_db, make_fund, make_member, make_requisite, make_user


def make_service(requisite_currency: str = "tjs", base_currency: str = "tjs"):
    db = make_db()
    service = ContributionService(db=db)
    service.accounts.get_active_requisite = AsyncMock(return_value=make_requisite(currency=requisite_currency))
    service.fund_repo.get = AsyncMock(return_value=make_fund(base_currency=base_currency))
    service.member_repo.get_by_user = AsyncMock(return_value=make_member())
    return db, service


def target_payload(target_fund_id: int = 1) -> ContributionCreateIn:
    return ContributionCreateIn(
        requisite_id=1,
        amount=1000,
        category=ContributionCategoryEnum.target_fund,
        target_fund_id=target_fund_id,
        receipt_image="data:image/png;base64,AAA",
    )


async def test_create_target_fund_not_found():
    db, service = make_service()
    service.target_fund_repo.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await service.create(fund_id=1, user_id=1, payload=target_payload(99))

    assert exc.value.status_code == 404
    db.commit.assert_not_called()


async def test_create_target_fund_closed():
    db, service = make_service()
    service.target_fund_repo.get = AsyncMock(return_value=SimpleNamespace(id=1, is_active=False, currency="tjs"))

    with pytest.raises(HTTPException) as exc:
        await service.create(fund_id=1, user_id=1, payload=target_payload())

    assert exc.value.status_code == 409


async def test_create_target_fund_in_other_currency_requires_credited_amount():
    db, service = make_service(requisite_currency="rub")
    service.target_fund_repo.get = AsyncMock(return_value=SimpleNamespace(id=1, is_active=True, currency="tjs"))

    with pytest.raises(HTTPException) as exc:
        await service.create(fund_id=1, user_id=1, payload=target_payload())

    assert exc.value.status_code == 422
    db.commit.assert_not_called()


async def test_create_monthly_fee_in_other_currency_requires_credited_amount():
    db, service = make_service(requisite_currency="usd", base_currency="tjs")

    payload = ContributionCreateIn(requisite_id=1, amount=15, receipt_image="data:image/png;base64,AAA")
    with pytest.raises(HTTPException) as exc:
        await service.create(fund_id=1, user_id=1, payload=payload)

    assert exc.value.status_code == 422
    db.commit.assert_not_called()


async def test_create_monthly_fee_in_other_currency_is_credited_in_base():
    db, service = make_service(requisite_currency="usd", base_currency="tjs")
    service.repo.create = AsyncMock(return_value=make_contribution())

    payload = ContributionCreateIn(
        requisite_id=1, amount=15, credited_amount=150, receipt_image="data:image/png;base64,AAA"
    )
    await service.create(fund_id=1, user_id=1, payload=payload)

    kwargs = service.repo.create.call_args.kwargs
    assert (kwargs["amount"], kwargs["currency"]) == (15, "usd")
    assert (kwargs["credited_amount"], kwargs["credited_currency"]) == (150, "tjs")
    assert kwargs["requisite_label"] == "Bank · 1111 2222 · Fund"


async def test_create_monthly_fee_takes_currency_and_unit():
    db, service = make_service()
    service.repo.create = AsyncMock(return_value=make_contribution())

    payload = ContributionCreateIn(requisite_id=1, amount=150, receipt_image="data:image/png;base64,AAA")
    await service.create(fund_id=1, user_id=1, payload=payload)

    kwargs = service.repo.create.call_args.kwargs
    assert kwargs["currency"] == "tjs"
    assert kwargs["credited_amount"] == 150
    assert kwargs["user_unit"] == "кв. 1"
    assert kwargs["billing_period"] is not None
    db.commit.assert_awaited_once()


def test_create_in_requires_target_fund_id():
    with pytest.raises(ValueError):
        ContributionCreateIn(
            requisite_id=1,
            amount=1000,
            category=ContributionCategoryEnum.target_fund,
            receipt_image="data:image/png;base64,AAA",
        )


async def test_approve_already_reviewed():
    db = make_db()
    service = ContributionService(db=db)
    service.repo.get = AsyncMock(return_value=make_contribution(status="approved"))

    with pytest.raises(HTTPException) as exc:
        await service.approve(fund_id=1, contribution_id=1, reviewer_id=2)

    assert exc.value.status_code == 409
    db.commit.assert_not_called()


async def test_reject_sets_reason_and_reviewer():
    db = make_db()
    contribution = make_contribution(status="pending")
    service = ContributionService(db=db)
    service.repo.get = AsyncMock(return_value=contribution)

    reviewer = make_user(id=2)
    contribution.reviewed_by = reviewer
    result = await service.reject(fund_id=1, contribution_id=1, reviewer_id=reviewer.id, reason="Чек обрезан")

    assert contribution.status == "rejected"
    assert contribution.comment_admin == "Чек обрезан"
    assert result.reviewed_by_name == reviewer.full_name
    db.commit.assert_awaited_once()


async def test_approve_corrects_credited_amount_only_for_other_currency():
    db = make_db()
    contribution = make_contribution(status="pending", amount=1300, currency="rub", credited_amount=150)
    service = ContributionService(db=db)
    service.repo.get = AsyncMock(return_value=contribution)

    await service.approve(fund_id=1, contribution_id=1, reviewer_id=2, credited_amount=140)
    assert contribution.credited_amount == 140

    same_currency = make_contribution(status="pending")
    service.repo.get = AsyncMock(return_value=same_currency)
    await service.approve(fund_id=1, contribution_id=1, reviewer_id=2, credited_amount=999)
    assert same_currency.credited_amount == 150

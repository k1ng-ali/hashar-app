"""Чеки в хранилище (R2): загрузка, привязка к взносу / расходу, подписанные ссылки, старые data URL."""

import base64
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.platform import uploads
from app.core import receipts, storage
from app.deps.fund import get_fund_context
from app.enums import CurrencyEnum, ExpenseCategoryEnum
from app.schemas.contribution import ContributionCreateIn
from app.schemas.expense import ExpenseCreateIn
from app.schemas.target_fund import TargetFundCreateIn, TargetFundUpdateIn
from app.services.contribution_service import ContributionService, contribution_out
from app.services.expense_service import ExpenseService, expense_out
from app.services.target_fund_service import TargetFundService
from tests.unit.helpers import (
    RECEIPT,
    make_contribution,
    make_ctx,
    make_db,
    make_fund,
    make_member,
    make_requisite,
)

PNG = base64.b64decode(RECEIPT.split(",", 1)[1])
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 32
SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg'/>"


async def uploaded_key(fund_id: int = 1, user_id: int = 1, data: bytes = PNG) -> str:
    return await receipts.upload_receipt(fund_id, user_id, data)


# ─── Загрузка ─────────────────────────────────────────────────────────────────


async def test_upload_puts_image_into_tmp(fake_storage):
    key = await uploaded_key(fund_id=3, user_id=7)
    assert receipts.UPLOAD_PATTERN.match(key) and key.startswith("tmp/3/7/") and key.endswith(".png")
    assert fake_storage.objects[key] == (PNG, "image/png")


async def test_upload_detects_format_by_content_not_name(fake_storage):
    key = await uploaded_key(data=WEBP)
    assert key.endswith(".webp") and fake_storage.objects[key][1] == "image/webp"


@pytest.mark.parametrize(
    "data", [b"<html><script>alert(1)</script>", b"GIF89a" + b"\x00" * 20, b"RIFF\x00\x00\x00\x00WAVE"]
)
async def test_upload_rejects_non_images(fake_storage, data):
    with pytest.raises(HTTPException) as error:
        await uploaded_key(data=data)
    assert error.value.status_code == 422
    assert not fake_storage.objects


# ─── Привязка к взносу / расходу ─────────────────────────────────────────────


async def test_store_moves_own_upload_to_receipts(fake_storage):
    key = await uploaded_key()
    stored = await receipts.store_receipt(key, fund_id=1, user_id=1)
    assert stored == f"receipts/1/{key.rsplit('/', 1)[1]}"
    assert fake_storage.objects[stored] == (PNG, "image/png")


@pytest.mark.parametrize("fund_id, user_id", [(1, 2), (2, 1)])
async def test_store_rejects_someone_elses_upload(fake_storage, fund_id, user_id):
    # Ключ чужой загрузки (другой участник или другой фонд) не даёт прикрепить чужой чек
    key = await uploaded_key(fund_id=1, user_id=1)
    with pytest.raises(HTTPException) as error:
        await receipts.store_receipt(key, fund_id=fund_id, user_id=user_id)
    assert error.value.status_code == 422


async def test_store_rejects_missing_upload():
    with pytest.raises(HTTPException) as error:
        await receipts.store_receipt(f"tmp/1/1/{'a' * 32}.png", fund_id=1, user_id=1)
    assert error.value.status_code == 422


async def test_store_uploads_legacy_data_url(fake_storage):
    # Старые версии приложения присылают чек base64 — он всё равно попадает в хранилище
    stored = await receipts.store_receipt(RECEIPT, fund_id=5, user_id=1)
    assert stored.startswith("receipts/5/") and stored.endswith(".png")
    assert fake_storage.objects[stored] == (PNG, "image/png")


async def test_store_keeps_demo_svg_in_db(fake_storage):
    assert await receipts.store_receipt(SVG, fund_id=1, user_id=1) == SVG
    assert not fake_storage.objects


@pytest.mark.parametrize(
    "value",
    [
        "receipts/1/" + "a" * 32 + ".png",  # готовый ключ не принимаем — только свою загрузку
        "tmp/1/1/../../receipts/1/" + "a" * 32 + ".png",
        "tmp/1/1/" + "a" * 32 + ".svg",
        "https://storage.test/tmp/1/1/" + "a" * 32 + ".png",
    ],
)
def test_schema_rejects_foreign_keys(value):
    with pytest.raises(ValidationError):
        ContributionCreateIn(requisite_id=1, amount=100, receipt_image=value)


# ─── Ссылки ───────────────────────────────────────────────────────────────────


def test_receipt_url_signs_keys_and_passes_data_urls():
    assert receipts.receipt_url("receipts/1/a.png") == "https://storage.test/receipts/1/a.png?signature=test"
    assert receipts.receipt_url(RECEIPT) == RECEIPT
    assert receipts.receipt_url(None) is None


def test_contribution_out_signs_receipt_only_when_visible():
    contribution = make_contribution(receipt_image="receipts/1/a.png")
    assert contribution_out(contribution).receipt_image.startswith("https://storage.test/receipts/1/a.png")
    assert contribution_out(contribution, show_receipt=False).receipt_image is None


# ─── Сервисы ──────────────────────────────────────────────────────────────────


async def test_contribution_create_stores_key_and_returns_link():
    service = ContributionService(db=make_db())
    service.accounts.get_active_requisite = AsyncMock(return_value=make_requisite())
    service.fund_repo.get = AsyncMock(return_value=make_fund())
    service.member_repo.get_by_user = AsyncMock(return_value=make_member())
    service.repo.create = AsyncMock(side_effect=lambda **fields: make_contribution(**fields))

    key = await uploaded_key()
    result = await service.create(1, 1, ContributionCreateIn(requisite_id=1, amount=150, receipt_image=key))

    stored = service.repo.create.await_args.kwargs["receipt_image"]
    assert stored.startswith("receipts/1/")
    assert result.receipt_image == f"https://storage.test/{stored}?signature=test"


async def test_expense_create_stores_every_receipt():
    service = ExpenseService(db=make_db())
    service.accounts.ensure_active_currency = AsyncMock()
    service.accounts.ensure_sufficient = AsyncMock()
    service.repo.create = AsyncMock(
        side_effect=lambda **fields: SimpleNamespace(
            id=1, target_fund=None, created_by=None, created_at=datetime.now(timezone.utc), **fields
        )
    )

    key = await uploaded_key(user_id=2)
    payload = ExpenseCreateIn(
        title="Ремонт",
        category=ExpenseCategoryEnum.repair,
        amount=100,
        currency=CurrencyEnum.tjs,
        description="Замена замка",
        receipt_images=[key, RECEIPT],
    )
    await service.create(1, 2, payload)

    images = service.repo.create.await_args.kwargs["receipt_images"]
    assert len(images) == 2 and all(image.startswith("receipts/1/") for image in images)


def test_expense_out_skips_unavailable_receipts(monkeypatch):
    # Локально без хранилища ключ подписать нечем — такой чек не отдаём, демо-чек остаётся
    def not_configured(key):
        raise storage.StorageNotConfigured(key)

    monkeypatch.setattr(storage, "presign_get", not_configured)
    expense = SimpleNamespace(
        id=1,
        title="Ремонт",
        category="repair",
        amount=100,
        currency="tjs",
        description="Замена замка",
        receipt_images=["receipts/1/a.png", SVG],
        target_fund_id=None,
        target_fund=None,
        created_by=None,
        created_at=datetime.now(timezone.utc),
    )
    assert expense_out(expense).receipt_images == [SVG]


# ─── Эндпоинт ─────────────────────────────────────────────────────────────────


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(uploads.router)
    app.dependency_overrides[get_fund_context] = lambda: make_ctx(user_id=4, fund_id=9)
    uploads.UPLOADS_BY_USER.reset("4")
    return TestClient(app)


def test_upload_endpoint_returns_key(client, fake_storage):
    response = client.post("/funds/9/uploads/receipt", files={"file": ("photo.jpg", PNG, "image/jpeg")})
    assert response.status_code == 201
    key = response.json()["key"]
    assert key.startswith("tmp/9/4/") and key.endswith(".png") and key in fake_storage.objects


def test_upload_endpoint_rejects_large_files(client, fake_storage):
    data = PNG + b"\x00" * receipts.MAX_UPLOAD_BYTES
    response = client.post("/funds/9/uploads/receipt", files={"file": ("photo.png", data, "image/png")})
    assert response.status_code == 413
    assert not fake_storage.objects


def test_upload_endpoint_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(uploads.UPLOADS_BY_USER, "limit", 2)
    statuses = [
        client.post("/funds/9/uploads/receipt", files={"file": ("p.png", PNG, "image/png")}).status_code
        for _ in range(3)
    ]
    assert statuses == [201, 201, 429]


# ─── Фото расхода и сбора ─────────────────────────────────────────────────────


def test_expense_accepts_at_most_three_images():
    fields = dict(
        title="Ремонт", category=ExpenseCategoryEnum.repair, amount=100, currency=CurrencyEnum.tjs, description="Замок"
    )
    assert len(ExpenseCreateIn(**fields, receipt_images=[RECEIPT] * 3).receipt_images) == 3
    with pytest.raises(ValidationError):
        ExpenseCreateIn(**fields, receipt_images=[RECEIPT] * 4)


def _target_service():
    service = TargetFundService(make_db())
    service.accounts.ensure_active_currency = AsyncMock()
    service.contribution_repo.collected_by_target_funds = AsyncMock(return_value={})
    service.repo.create = AsyncMock(
        side_effect=lambda **fields: SimpleNamespace(id=1, is_active=True, created_at=datetime.now(timezone.utc), **fields)
    )
    return service


TARGET_FIELDS = dict(title="Шлагбаум", description="Во двор", target_amount=1000, currency=CurrencyEnum.tjs)


async def test_target_fund_photo_is_optional(fake_storage):
    out = await _target_service().create(1, 2, TargetFundCreateIn(**TARGET_FIELDS))
    assert out.image is None


async def test_target_fund_photo_is_stored_and_signed(fake_storage):
    service = _target_service()
    key = await uploaded_key(user_id=2)
    out = await service.create(1, 2, TargetFundCreateIn(**TARGET_FIELDS, image=key))

    stored = service.repo.create.await_args.kwargs["image"]
    assert stored.startswith("receipts/1/") and stored in fake_storage.objects
    assert out.image and out.image != stored


async def test_target_fund_photo_of_another_user_is_rejected(fake_storage):
    key = await uploaded_key(user_id=9)
    with pytest.raises(HTTPException) as error:
        await _target_service().create(1, 2, TargetFundCreateIn(**TARGET_FIELDS, image=key))
    assert error.value.status_code == 422


async def test_target_fund_update_keeps_replaces_or_removes_photo(fake_storage):
    service = _target_service()
    target = SimpleNamespace(
        id=1, fund_id=1, image="receipts/1/old.png", is_active=True, created_at=datetime.now(timezone.utc),
        **{**TARGET_FIELDS, "currency": "tjs"}, category="landscaping",
    )
    service.repo.get = AsyncMock(return_value=target)

    await service.update(1, 1, 2, TargetFundUpdateIn(title="Новый шлагбаум"))
    assert target.image == "receipts/1/old.png"

    await service.update(1, 1, 2, TargetFundUpdateIn(image=await uploaded_key(user_id=2)))
    assert target.image.startswith("receipts/1/") and target.image != "receipts/1/old.png"

    await service.update(1, 1, 2, TargetFundUpdateIn(image=None))
    assert target.image is None


async def test_target_fund_update_is_audited_with_old_and_new_values(fake_storage):
    service = _target_service()
    service.audit.add = Mock()
    target = SimpleNamespace(
        id=1, fund_id=1, image=None, is_active=True, created_at=datetime.now(timezone.utc),
        **{**TARGET_FIELDS, "currency": "tjs"}, category="landscaping",
    )
    service.repo.get = AsyncMock(return_value=target)

    # Те же значения — правки нет, журнал не засоряем
    await service.update(1, 1, 2, TargetFundUpdateIn(title="Шлагбаум", target_amount=1000))
    service.audit.add.assert_not_called()

    await service.update(1, 1, 2, TargetFundUpdateIn(title="Шлагбаум", target_amount=1500))
    details = service.audit.add.call_args.kwargs["details"]
    assert service.audit.add.call_args.kwargs["action"] == "target_fund.update"
    assert details["changes"] == {"target_amount": [1000, 1500]}

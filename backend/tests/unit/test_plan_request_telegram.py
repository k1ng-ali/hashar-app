"""Уведомление админу платформы в Telegram о новой заявке на тариф."""

import io
import urllib.error
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import BackgroundTasks

from app.core import telegram
from app.core.config import settings
from app.enums import PlanEnum
from app.schemas.plan import PlanRequestIn
from app.services.plan_service import PlanService, plan_request_message
from app.services.pricing_service import ResolvedPrice
from tests.unit.helpers import make_db, make_fund, make_user

NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
TOKEN = "123456:secret-bot-token"


@pytest.fixture
def telegram_on(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", TOKEN)
    monkeypatch.setattr(settings, "TELEGRAM_ADMIN_CHAT_ID", "42")
    sent = []
    monkeypatch.setattr(telegram, "_post", sent.append)
    return sent


def make_request(fund, plan="pro", months=1, **extra):
    fields = dict(
        id=7,
        fund_id=fund.id,
        fund=fund,
        plan=plan,
        months=months,
        status="pending",
        contact="@chairman",
        comment=None,
        admin_comment=None,
        requested_by=make_user(id=3, full_name="Али Валиев"),
        reviewed_at=None,
        created_at=NOW,
        list_price_tjs={"pro": 199, "max": 399}.get(plan),
        price_tjs={"pro": 199, "max": 399}.get(plan),
        discount_id=None,
        discount_label=None,
        discount_months=0,
    )
    fields.update(extra)
    return SimpleNamespace(**fields)


# ─── Текст сообщения ──────────────────────────────────────────────────────────


def test_message_for_extension():
    fund = make_fund(id=5, name="Дом 12", plan="pro", plan_price=199, plan_expires_at=NOW + timedelta(days=10))

    text = plan_request_message(make_request(fund, months=3), now=NOW)

    assert "Продление тарифа" in text
    assert "Дом 12" in text and "#5" in text
    assert "Pro × 3 мес. — 597 смн" in text
    assert "Сейчас: Pro до 08.11.2026" in text
    assert "Остаток" not in text  # продление — просто плюс месяцы, без переноса
    assert "Али Валиев" in text and "@chairman" in text


def test_message_shows_discount():
    request = make_request(make_fund(), price_tjs=99, discount_label="SALE<50>", discount_months=1)

    text = plan_request_message(request, now=NOW)

    assert "Pro × 1 мес. — 99 смн" in text
    assert "Скидка: SALE&lt;50&gt; — 99 вместо 199 смн/мес, мес. со скидкой: 1" in text


def test_message_for_plan_change_shows_carryover():
    fund = make_fund(plan="max", plan_price=399, plan_expires_at=NOW + timedelta(days=15))

    text = plan_request_message(make_request(fund, plan="pro"), now=NOW)

    assert "Смена тарифа" in text
    assert "Остаток текущего: 199.5 смн → +30 дн. нового" in text


def test_message_for_free_fund_and_individual_plan():
    text = plan_request_message(make_request(make_fund(plan="free"), plan="individual"), now=NOW)

    assert "Подключение тарифа" in text
    assert "Сейчас: Free" in text
    assert "цена по договорённости" in text


def test_message_escapes_user_text():
    fund = make_fund(name="<b>Фонд</b> & Co")

    text = plan_request_message(make_request(fund, contact="<a href='x'>", comment="1 < 2"), now=NOW)

    assert "&lt;b&gt;Фонд&lt;/b&gt; &amp; Co" in text
    assert "<a href='x'>" not in text
    assert "Комментарий: 1 &lt; 2" in text


def test_message_links_to_requests_tab(monkeypatch):
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["https://hashar.app"])

    text = plan_request_message(make_request(make_fund()), now=NOW)

    assert '<a href="https://hashar.app/platform?tab=requests">' in text


# ─── Создание заявки ──────────────────────────────────────────────────────────


async def test_create_request_notifies_admin_after_response():
    service = PlanService(db=make_db())
    service.repo.has_pending = AsyncMock(return_value=False)
    service.repo.create = AsyncMock(return_value=make_request(make_fund(name="Дом 12")))
    service.fund_repo.get = AsyncMock(return_value=make_fund())
    service.pricing.resolve = AsyncMock(return_value=ResolvedPrice(list_price=199, price=199))
    tasks = BackgroundTasks()

    await service.create_request(
        fund_id=1,
        user_id=3,
        payload=PlanRequestIn(plan=PlanEnum.pro, contact="@chairman"),
        background_tasks=tasks,
    )

    service.db.commit.assert_awaited_once()
    [task] = tasks.tasks
    assert task.func is telegram.notify_admin
    assert "Дом 12" in task.args[0]


# ─── Отправка ─────────────────────────────────────────────────────────────────


async def test_notify_disabled_without_settings(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "")
    post = MagicMock()
    monkeypatch.setattr(telegram, "_post", post)

    await telegram.notify_admin("hi")

    post.assert_not_called()


async def test_notify_sends_when_configured(telegram_on):
    await telegram.notify_admin("hi")

    assert telegram_on == ["hi"]


@pytest.mark.parametrize(
    "error",
    [
        urllib.error.HTTPError(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage", 403, "Forbidden", {}, io.BytesIO(b"bot was blocked")
        ),
        urllib.error.URLError(f"https://api.telegram.org/bot{TOKEN}/sendMessage timed out"),
    ],
)
async def test_notify_swallows_errors_without_leaking_token(monkeypatch, caplog, error):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", TOKEN)
    monkeypatch.setattr(settings, "TELEGRAM_ADMIN_CHAT_ID", "42")
    monkeypatch.setattr(telegram, "_post", MagicMock(side_effect=error))

    await telegram.notify_admin("hi")

    assert "Telegram" in caplog.text
    assert TOKEN not in caplog.text

"""
Уведомления админу платформы в Telegram — новые заявки на тариф.

- бот создаётся у @BotFather (можно тот же, что у мониторинга, monitoring/README.md);
  TELEGRAM_ADMIN_CHAT_ID — личный чат админа с ботом или группа, куда бот добавлен
- без TELEGRAM_BOT_TOKEN или TELEGRAM_ADMIN_CHAT_ID уведомления выключены
- уведомление не должно ломать запрос: ошибки отправки только пишутся в лог
- токен бота входит в адрес запроса, поэтому адрес в лог не пишем
"""

import asyncio
import html
import json
import logging
import urllib.error
import urllib.request

from app.core.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"
TELEGRAM_TIMEOUT_SECONDS = 10


def telegram_enabled() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ADMIN_CHAT_ID)


def escape(value: object) -> str:
    """Текст от пользователей (название фонда, контакт) — в HTML-разметку сообщения."""
    return html.escape(str(value), quote=False)


def _post(text: str) -> None:
    body = {
        "chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    request = urllib.request.Request(
        TELEGRAM_SEND_URL.format(token=settings.TELEGRAM_BOT_TOKEN),
        data=json.dumps(body).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=TELEGRAM_TIMEOUT_SECONDS):
        return


async def notify_admin(text: str) -> None:
    """Сообщение в чат админа (HTML-разметка Telegram). Исключений не бросает."""
    if not telegram_enabled():
        return
    try:
        await asyncio.to_thread(_post, text)
    except urllib.error.HTTPError as error:
        # 400 — неверная разметка или chat id, 401 — неверный токен, 403 — бот не добавлен в чат
        logger.warning("Telegram responded %s: %s", error.code, error.read()[:500].decode(errors="replace"))
    except OSError as error:
        logger.warning("Telegram is unreachable: %s", error.__class__.__name__)

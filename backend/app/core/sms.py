"""
Отправка SMS через Payomchi (https://payomchi.tj/api-docs) — коды подтверждения личности.

Payomchi доставляет только на таджикские номера (+992), поэтому подтверждение по SMS
доступно только им; остальные подтверждают личность через Google.

- номер передаётся цифрами с кодом страны, без «+»: 992901234567
- Idempotency-Key: повтор того же запроса (ретрай после таймаута) не отправит SMS второй раз
- без PAYOMCHI_API_KEY в DEV_MODE код не отправляется, а пишется в лог
"""

import asyncio
import json
import logging
import urllib.error
import urllib.request

from app.core.config import settings

logger = logging.getLogger(__name__)

PAYOMCHI_SMS_URL = "https://api.payomchi.tj/api/v1/user/sms"
SMS_TIMEOUT_SECONDS = 10
# +992 и 9 цифр абонента
TJ_PREFIX = "+992"
TJ_PHONE_LENGTH = 13


class SmsError(Exception):
    """SMS не ушло: сеть, неверный ключ, кончилась квота или сбой у провайдера."""


class SmsRejectedPhone(SmsError):
    """Провайдер не принял номер (400)."""


def is_sms_phone(phone: str | None) -> bool:
    """Номер, на который можно отправить код: таджикский, в виде +992XXXXXXXXX."""
    return bool(phone) and phone.startswith(TJ_PREFIX) and len(phone) == TJ_PHONE_LENGTH and phone[1:].isdigit()


def sms_enabled() -> bool:
    return bool(settings.PAYOMCHI_API_KEY) or settings.DEV_MODE


def _post(phone: str, message: str, idempotency_key: str) -> None:
    body = {"phone": phone.lstrip("+"), "message": message, "channel": "sms"}
    if settings.PAYOMCHI_SENDER_ID:
        body["senderId"] = settings.PAYOMCHI_SENDER_ID
    request = urllib.request.Request(
        PAYOMCHI_SMS_URL,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "X-Api-Key": settings.PAYOMCHI_API_KEY,
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=SMS_TIMEOUT_SECONDS):
            return
    except urllib.error.HTTPError as error:
        detail = error.read()[:500].decode(errors="replace")
        # 409 — этот Idempotency-Key уже обработан: SMS уже отправлено
        if error.code == 409:
            return
        logger.warning("Payomchi responded %s: %s", error.code, detail)
        if error.code == 400:
            raise SmsRejectedPhone(detail) from error
        raise SmsError(f"Payomchi responded {error.code}") from error
    except OSError as error:
        logger.warning("Payomchi is unreachable: %s", error)
        raise SmsError("Payomchi is unreachable") from error


async def send_sms(phone: str, message: str, idempotency_key: str) -> None:
    if not settings.PAYOMCHI_API_KEY:
        if not settings.DEV_MODE:
            raise SmsError("PAYOMCHI_API_KEY is not set")
        logger.warning("DEV_MODE: SMS to %s not sent: %s", phone, message)
        return
    await asyncio.to_thread(_post, phone, message, idempotency_key)

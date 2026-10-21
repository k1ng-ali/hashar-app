"""
Фоновые задачи процесса API.

Запускаются в lifespan приложения в каждом воркере uvicorn — поэтому задачи
идемпотентны (уведомления о тарифе защищены dedupe_key, см. models/fund_notice.py).
"""

import asyncio
import logging

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.notice_service import NoticeService

logger = logging.getLogger(__name__)

# Первая проверка — вскоре после старта, а не сразу: не мешаем запуску и миграциям
START_DELAY = 30


async def plan_expiry_loop() -> None:
    """Уведомления совету: за 3 дня до окончания тарифа, при окончании и при блокировке взносов."""
    await asyncio.sleep(START_DELAY)
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await NoticeService(db=db).check_plan_expiry()
        except Exception:  # noqa: BLE001 — задача не должна умирать из-за одного сбоя
            logger.exception("Plan expiry check failed")
        await asyncio.sleep(settings.NOTICE_CHECK_INTERVAL)

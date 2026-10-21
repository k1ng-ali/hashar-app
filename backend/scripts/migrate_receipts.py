"""
Перенос чеков из БД в хранилище: data URL (base64) → объект receipts/{fund_id}/... и ключ в БД.

Запуск из папки backend (в проде — `docker compose exec backend python -m scripts.migrate_receipts`):
    python -m scripts.migrate_receipts            # перенести
    python -m scripts.migrate_receipts --dry-run  # только посчитать

Перед запуском — бэкап БД (deploy/backup.sh). Скрипт можно прерывать и запускать снова:
каждая пачка коммитится, перенесённые записи больше не содержат data URL и пропускаются.
Демо-чеки SVG не переносятся — они остаются в БД как есть.
"""

import asyncio
import sys

from sqlalchemy import String, cast, func, or_, select

from app.core.database import AsyncSessionLocal
from app.core.receipts import RASTER_PATTERN, store_receipt
from app.models import Contribution, Expense

BATCH = 50
RASTER_PREFIXES = ("data:image/png", "data:image/jpeg", "data:image/webp")


def _is_raster(value: str) -> bool:
    return value.startswith(RASTER_PREFIXES)


async def _upload(value: str, fund_id: int) -> str:
    # Битый data URL оставляем как есть: он и раньше не показывался, а скрипт не должен падать на одной записи
    if not RASTER_PATTERN.match(value):
        print(f"  пропущен некорректный чек фонда {fund_id}")
        return value
    # user_id не нужен: для data URL store_receipt не проверяет владельца загрузки
    return await store_receipt(value, fund_id, user_id=0)


async def migrate_contributions(dry_run: bool) -> int:
    condition = or_(*(Contribution.receipt_image.startswith(prefix) for prefix in RASTER_PREFIXES))
    last_id = moved = 0
    async with AsyncSessionLocal() as db:
        total = await db.scalar(select(func.count()).select_from(Contribution).where(condition))
        print(f"Взносы: {total} чеков в БД")
        if dry_run:
            return total
        while True:
            rows = (
                await db.scalars(
                    select(Contribution)
                    .where(condition, Contribution.id > last_id)
                    .order_by(Contribution.id)
                    .limit(BATCH)
                )
            ).all()
            if not rows:
                break
            for contribution in rows:
                contribution.receipt_image = await _upload(contribution.receipt_image, contribution.fund_id)
                moved += 1
            last_id = rows[-1].id
            await db.commit()
            print(f"  перенесено {moved} / {total}")
    return moved


async def migrate_expenses(dry_run: bool) -> int:
    # receipt_images — JSONB-список; ищем по тексту, а заменяем поэлементно
    condition = or_(*(cast(Expense.receipt_images, String).contains(prefix) for prefix in RASTER_PREFIXES))
    last_id = moved = 0
    async with AsyncSessionLocal() as db:
        total = await db.scalar(select(func.count()).select_from(Expense).where(condition))
        print(f"Расходы: {total} записей с чеками в БД")
        if dry_run:
            return total
        while True:
            rows = (
                await db.scalars(
                    select(Expense).where(condition, Expense.id > last_id).order_by(Expense.id).limit(BATCH)
                )
            ).all()
            if not rows:
                break
            for expense in rows:
                expense.receipt_images = [
                    await _upload(image, expense.fund_id) if _is_raster(image) else image
                    for image in expense.receipt_images
                ]
                moved += 1
            last_id = rows[-1].id
            await db.commit()
            print(f"  перенесено {moved} / {total}")
    return moved


async def main() -> None:
    dry_run = "--dry-run" in sys.argv
    contributions = await migrate_contributions(dry_run)
    expenses = await migrate_expenses(dry_run)
    action = "К переносу" if dry_run else "Перенесено"
    print(f"{action}: чеков взносов — {contributions}, расходов с чеками — {expenses}")


if __name__ == "__main__":
    asyncio.run(main())

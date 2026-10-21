"""
Чеки: проверка, сохранение в хранилище (core/storage.py) и ссылки на просмотр.

Чек показывается другим участникам, поэтому принимаем только настоящие растровые
картинки PNG / JPEG / WebP с проверкой сигнатуры файла и размера. Любая другая строка
(javascript:, http-ссылка, html) отклоняется — иначе её можно подсунуть совету как «чек».

Путь чека:
1. Фронтенд сжимает фото и загружает файлом в POST /funds/{id}/uploads/receipt →
   объект tmp/{fund_id}/{user_id}/{uuid}.{ext}, в ответ — этот ключ.
   Незавершённые загрузки удаляет правило жизненного цикла бакета (префикс tmp/, 1 день).
2. Взнос / расход приходит с ключом. store_receipt проверяет, что загрузка своя,
   и копирует её в receipts/{fund_id}/{uuid}.{ext} — этот ключ и пишется в БД.
3. При выдаче receipt_url превращает ключ в подписанную ссылку.

Старые версии приложения присылают чек data URL (data:image/...;base64,...) — его
store_receipt сам загружает в хранилище. SVG data URL принимаем только в DEV_MODE: это
демо-чеки из генератора на фронтенде, они остаются в БД как есть.
"""

import base64
import binascii
import re
import uuid

from fastapi import HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.core import storage
from app.core.config import settings

# Предел для загруженного файла. Фронтенд сжимает фото до 1600 px — это 150–500 КБ
MAX_UPLOAD_BYTES = int(1.5 * 1024 * 1024)
# Предел для data URL от старых версий приложения (они сжимали до 3 МБ)
MAX_RECEIPT_BYTES = 3 * 1024 * 1024
# Предел длины строки — base64 раздувает данные на треть, плюс префикс
MAX_RECEIPT_CHARS = MAX_RECEIPT_BYTES * 4 // 3 + 64

RASTER_PATTERN = re.compile(r"^data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/]+={0,2})$")
SVG_PREFIX = "data:image/svg+xml;utf8,"
UPLOAD_PATTERN = re.compile(r"^tmp/(\d+)/(\d+)/([0-9a-f]{32}\.(?:png|jpg|webp))$")

EXTENSIONS = {"png": "png", "jpeg": "jpg", "webp": "webp"}
CONTENT_TYPES = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}


def detect_format(head: bytes) -> str | None:
    """Формат картинки по первым байтам файла: png / jpeg / webp или None."""
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "webp"
    return None


def validate_receipt(value: str) -> str:
    """Схемы: ключ загрузки, растровый data URL или демо-SVG. Возвращает значение или ValueError."""
    if UPLOAD_PATTERN.match(value):
        return value
    if settings.DEV_MODE and value.startswith(SVG_PREFIX):
        return value

    match = RASTER_PATTERN.match(value)
    if not match:
        raise ValueError("receipt must be an uploaded image key or a PNG, JPEG or WebP data URL")

    image_format, data = match.groups()
    if len(data) * 3 // 4 > MAX_RECEIPT_BYTES:
        raise ValueError("receipt image is too large")
    try:
        head = base64.b64decode(data[:24], validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("receipt image is corrupted")
    if detect_format(head) != image_format:
        raise ValueError("receipt content does not match its type")
    return value


def _storage_unavailable() -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Receipt storage is not configured")


async def upload_receipt(fund_id: int, user_id: int, data: bytes) -> str:
    """Загруженный файл → объект tmp/... Возвращает ключ для взноса или расхода."""
    image_format = detect_format(data[:16])
    if not image_format:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Receipt must be a PNG, JPEG or WebP image"
        )
    key = f"tmp/{fund_id}/{user_id}/{uuid.uuid4().hex}.{EXTENSIONS[image_format]}"
    try:
        await run_in_threadpool(storage.put_object, key, data, CONTENT_TYPES[image_format])
    except storage.StorageNotConfigured:
        raise _storage_unavailable()
    return key


async def store_receipt(value: str, fund_id: int, user_id: int) -> str:
    """Проверенный схемой чек → значение для БД: ключ в receipts/ (или демо-SVG как есть)."""
    if value.startswith(SVG_PREFIX):
        return value

    try:
        if value.startswith("data:"):
            image_format, data = RASTER_PATTERN.match(value).groups()
            key = f"receipts/{fund_id}/{uuid.uuid4().hex}.{EXTENSIONS[image_format]}"
            await run_in_threadpool(storage.put_object, key, base64.b64decode(data), CONTENT_TYPES[image_format])
            return key

        # Ключ загрузки: только свой и в этот же фонд — чужой ключ не даёт прикрепить чужой чек
        upload_fund_id, upload_user_id, name = UPLOAD_PATTERN.match(value).groups()
        key = f"receipts/{fund_id}/{name}"
        if (int(upload_fund_id), int(upload_user_id)) != (fund_id, user_id) or not await run_in_threadpool(
            storage.copy_object, value, key
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Receipt upload not found, upload it again"
            )
        return key
    except storage.StorageNotConfigured:
        raise _storage_unavailable()


def receipt_url(value: str | None) -> str | None:
    """Значение из БД → то, что видит фронтенд: подписанная ссылка или data URL как есть."""
    if not value or value.startswith("data:"):
        return value
    try:
        return storage.presign_get(value)
    except storage.StorageNotConfigured:
        # Локально без MinIO: запись есть, а показать файл нечем
        return None

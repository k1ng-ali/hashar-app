"""
Проверка чеков: картинка в виде data URL.

Чек хранится в БД и показывается другим участникам, поэтому принимаем только
настоящие растровые картинки: data:image/(png|jpeg|webp);base64,... с проверкой
сигнатуры файла и размера. Любая другая строка (javascript:, http-ссылка, html)
отклоняется — иначе её можно подсунуть совету как «чек».

SVG принимаем только в DEV_MODE: это демо-чеки из генератора на фронтенде.
"""

import base64
import binascii
import re

from app.core.config import settings

# Предел для одного чека после декодирования. Фронтенд сжимает фото до ~0.5 МБ
MAX_RECEIPT_BYTES = 3 * 1024 * 1024
# Предел длины строки — base64 раздувает данные на треть, плюс префикс
MAX_RECEIPT_CHARS = MAX_RECEIPT_BYTES * 4 // 3 + 64

RASTER_PATTERN = re.compile(r"^data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/]+={0,2})$")
SVG_PREFIX = "data:image/svg+xml;utf8,"

# Сигнатуры форматов (первые байты файла)
SIGNATURES = {
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpeg": (b"\xff\xd8\xff",),
    "webp": (b"RIFF",),
}


def validate_receipt(value: str) -> str:
    """Возвращает чек без изменений или ValueError с причиной."""
    if settings.DEV_MODE and value.startswith(SVG_PREFIX):
        return value

    match = RASTER_PATTERN.match(value)
    if not match:
        raise ValueError("receipt must be a PNG, JPEG or WebP image (data URL)")

    image_format, data = match.groups()
    if len(data) * 3 // 4 > MAX_RECEIPT_BYTES:
        raise ValueError("receipt image is too large")
    try:
        head = base64.b64decode(data[:24], validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("receipt image is corrupted")
    if not head.startswith(SIGNATURES[image_format]):
        raise ValueError("receipt content does not match its type")
    if image_format == "webp" and head[8:12] != b"WEBP":
        raise ValueError("receipt content does not match its type")
    return value

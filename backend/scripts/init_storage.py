"""
Проверка хранилища чеков; локально — создание бакета.

Запуск из папки backend:
    python -m scripts.init_storage

- бакет есть — печатает «готово» (так же проверяется доступ к Cloudflare R2 в проде)
- бакета нет и DEV_MODE — создаёт его (локальный RustFS из docker-compose)
- бакета нет в проде — ошибка: бакет R2 создаётся в дашборде Cloudflare,
  у токена бэкенда прав на это нет (и не должно быть)
"""

import sys

from botocore.exceptions import ClientError

from app.core import storage
from app.core.config import settings


def init_storage() -> None:
    if not settings.storage_configured:
        print("Хранилище не настроено (S3_*) — загрузка чеков выключена, пропускаю")
        return

    client = storage._client()
    try:
        client.head_bucket(Bucket=settings.S3_BUCKET)
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") not in ("404", "NoSuchBucket") or not settings.DEV_MODE:
            sys.exit(f"Бакет {settings.S3_BUCKET} недоступен: {error}")
        client.create_bucket(Bucket=settings.S3_BUCKET)
        print(f"Создан бакет {settings.S3_BUCKET}")
    print(f"Хранилище готово: {settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET}")


if __name__ == "__main__":
    init_storage()

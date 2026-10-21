"""
Хранилище файлов по S3 API: в проде Cloudflare R2, локально MinIO.

Бакет приватный: публичного домена нет, файл открывается только по подписанной
ссылке (presign_get), которую бэкенд выдаёт тем, кому файл положено видеть.
В БД хранится ключ объекта, а не ссылка, — ссылки живут S3_URL_TTL секунд.

Клиент boto3 синхронный: сетевые вызовы (put/copy) из async-кода — через run_in_threadpool.
Подпись ссылки считается локально, без запроса в хранилище, её можно звать напрямую.
"""

from functools import lru_cache

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageNotConfigured(RuntimeError):
    pass


@lru_cache
def _client() -> BaseClient:
    if not settings.storage_configured:
        raise StorageNotConfigured("S3 storage is not configured")
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
        config=Config(
            signature_version="s3v4",
            # R2 и MinIO работают с путём /<bucket>/<key>, без поддомена на бакет
            s3={"addressing_style": "path"},
            connect_timeout=5,
            read_timeout=20,
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )


def put_object(key: str, data: bytes, content_type: str, metadata: dict[str, str] | None = None) -> None:
    _client().put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
        # Ключ уникален и файл не меняется — браузер может кешировать сколько угодно
        CacheControl="private, max-age=31536000, immutable",
        Metadata=metadata or {},
    )


def copy_object(source_key: str, key: str) -> bool:
    """Копия внутри бакета. False — исходного объекта нет."""
    try:
        _client().copy_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
            CopySource={"Bucket": settings.S3_BUCKET, "Key": source_key},
        )
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return False
        raise
    return True


def presign_get(key: str) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=settings.S3_URL_TTL,
    )

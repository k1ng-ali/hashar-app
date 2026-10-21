import os

import pytest

# Настройки для тестов: БД не нужна, сервисы работают с замоканной сессией
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")


# После настроек: app.core.config читает окружение при импорте
from app.core import storage  # noqa: E402


class FakeStorage:
    """Хранилище чеков в памяти вместо R2: put / copy / подписанная ссылка."""

    def __init__(self):
        self.objects: dict[str, tuple[bytes, str]] = {}

    def put_object(self, key: str, data: bytes, content_type: str, metadata=None) -> None:
        self.objects[key] = (data, content_type)

    def copy_object(self, source_key: str, key: str) -> bool:
        if source_key not in self.objects:
            return False
        self.objects[key] = self.objects[source_key]
        return True

    def presign_get(self, key: str) -> str:
        return f"https://storage.test/{key}?signature=test"


@pytest.fixture(autouse=True)
def fake_storage(monkeypatch) -> FakeStorage:
    fake = FakeStorage()
    for name in ("put_object", "copy_object", "presign_get"):
        monkeypatch.setattr(storage, name, getattr(fake, name))
    return fake

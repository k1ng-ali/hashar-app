import os

# Настройки для тестов: БД не нужна, сервисы работают с замоканной сессией
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")

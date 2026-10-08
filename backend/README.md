# Бэкенд фонда дома (FastAPI + PostgreSQL + SQLAlchemy + Alembic + Docker)

Полнофункциональный бэкенд для системы прозрачного управления локальным общественным фондом многоквартирного дома (ТСЖ / ЖК).

## Стек технологий

- **Язык**: Python 3.10+
- **Фреймворк**: [FastAPI](https://fastapi.tiangolo.com/) (асинхронный REST API, автогенерация Swagger/OpenAPI)
- **База данных**: PostgreSQL 16
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Миграции**: [Alembic](https://alembic.sqlalchemy.org/)
- **Валидация и сериализация данных**: [Pydantic v2](https://docs.pydantic.dev/) + `pydantic-settings`
- **Контейнеризация**: Docker и Docker Compose

---

## Архитектура проекта

```
backend/
├── alembic/                         # Миграции базы данных
│   ├── versions/                    # Файлы ревизий
│   │   └── 001_initial_schema.py    # Базовая схема таблиц
│   ├── env.py                       # Окружение мигратора Alembic
│   └── script.py.mako               # Шаблон новых миграций
├── alembic.ini                      # Конфигурация Alembic
├── app/
│   ├── api/                         # Маршруты и контроллеры
│   │   ├── deps.py                  # Внедрение зависимостей (Auth, DB, RBAC)
│   │   └── v1/
│   │       ├── api.py               # Роутер API v1
│   │       └── endpoints/           # Эндпоинты по доменам
│   │           ├── auth.py          # Логин, выдача JWT токенов, /me
│   │           ├── users.py         # Список собственников, статусы оплат
│   │           ├── contributions.py # Взносы, прикрепление чеков, верификация
│   │           ├── expenses.py      # Расходы фонда, чеки и акты
│   │           ├── target_funds.py  # Целевые сборы, прогресс накоплений
│   │           ├── announcements.py # Доска объявлений, комментарии, лайки
│   │           ├── settings.py      # Тарифы и банковские реквизиты
│   │           └── reports.py       # Финансовые отчеты и экспорт CSV
│   ├── core/                        # Ядро приложения
│   │   ├── config.py                # Настройки (pydantic-settings, .env)
│   │   ├── database.py              # Сессии SQLAlchemy, engine
│   │   └── security.py              # Хеширование паролей, генерация JWT
│   ├── models/                      # SQLAlchemy ORM модели
│   │   ├── user.py                  # Пользователи и роли (SUPERADMIN, ADMIN, RESIDENT)
│   │   ├── rate.py                  # Тариф ежемесячного взноса
│   │   ├── target_fund.py           # Целевые сборы
│   │   ├── contribution.py          # Взносы и чеки
│   │   ├── expense.py               # Расходы
│   │   ├── requisite.py             # Реквизиты для перевода
│   │   └── announcement.py          # Объявления и комментарии
│   ├── schemas/                     # Pydantic DTO схемы
│   └── services/                    # Бизнес-логика (расчет задолженностей и сальдо)
├── Dockerfile                       # Сборка контейнера бэкенда
├── requirements.txt                 # Зависимости Python
├── seed.py                          # Скрипт наполнения тестовыми данными
└── README.md
```

---

## Локальная разработка (рекомендуемый способ)

В текущем режиме Docker запускает только PostgreSQL, а FastAPI запускается локально с hot reload:

```bash
docker compose up -d db
..\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
..\.venv\Scripts\python.exe backend\seed.py
..\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Сервисы будут доступны по адресам:
- **FastAPI Backend**: [http://localhost:8000](http://localhost:8000)
- **Интерактивная документация Swagger UI**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Альтернативная документация ReDoc**: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
- **PostgreSQL**: `localhost:15432` (логин: `postgres`, пароль: `postgres_password`, БД: `fund_db`)

Frontend запускается из корня проекта отдельной командой `npm run dev`.

---

## Локальный запуск без Docker

### 1. Установка зависимостей
```bash
cd backend
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Применение миграций Alembic
```bash
alembic upgrade head
```

### 3. Заполнение тестовыми данными
```bash
python seed.py
```

### 4. Запуск сервера разработки Uvicorn
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Ролевая модель доступа (RBAC)

API строго разграничивает права на основе роли:
- **RESIDENT (Жилец)**: подача взносов с чеками, просмотр истории своих оплат, чтение и комментирование объявлений, просмотр отчетов.
- **ADMIN (Член совета дома)**: верификация и отклонение чеков, добавление расходов фонда, открытие целевых сборов, публикация закрепленных объявлений.
- **SUPERADMIN (Председатель дома)**: изменение тарифа взносов, добавление реквизитов карт/счетов, назначение ролей жильцов.

---

## Основные эндпоинты API

| Метод | Путь | Описание | Доступ |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Получение JWT токена | Публичный |
| `GET` | `/api/v1/auth/me` | Данные текущего пользователя | Авторизованный |
| `GET` | `/api/v1/users/` | Список собственников помещений | Авторизованный |
| `GET` | `/api/v1/users/{id}/status` | Расчет задолженности жильца | Авторизованный |
| `GET` | `/api/v1/contributions/` | Реестр платежей (с фильтрами) | Авторизованный |
| `POST` | `/api/v1/contributions/` | Внесение взноса с прикреплением чека | Собственник |
| `POST` | `/api/v1/contributions/{id}/verify` | Одобрение или отклонение чека | Совет / Председатель |
| `GET` | `/api/v1/expenses/` | Перечень произведенных расходов | Авторизованный |
| `POST` | `/api/v1/expenses/` | Добавление расхода с чеком | Совет / Председатель |
| `GET` | `/api/v1/target-funds/` | Целевые сборы с прогресс-баром | Все |
| `POST` | `/api/v1/target-funds/` | Создание нового целевого сбора | Совет / Председатель |
| `GET` | `/api/v1/announcements/` | Доска объявлений дома | Все |
| `POST` | `/api/v1/announcements/` | Публикация объявления | Авторизованный |
| `GET` | `/api/v1/reports/summary` | Сводная статистика для карточек | Все |
| `GET` | `/api/v1/reports/financial` | Помесячная ведомость (2026 г.) | Все |
| `GET` | `/api/v1/reports/export/contributions` | Скачать выгрузку взносов в CSV | Авторизованный |
| `GET` | `/api/v1/reports/export/expenses` | Скачать реестр расходов в CSV | Авторизованный |

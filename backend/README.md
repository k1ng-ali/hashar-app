# Fund System — backend

Платформа фондов домов (ТСЖ / ЖК / посёлков): пользователь регистрируется, создаёт свой фонд или вступает в существующий по коду / ссылке / названию. Внутри фонда — взносы с чеками и их проверка советом, расходы, целевые сборы, мультивалютные счета с переводами, доска объявлений и отчётность. Тарифы платформы подтверждает её администратор.

**Стек:** Python 3.12 · FastAPI · SQLAlchemy 2 (async, asyncpg) · PostgreSQL 16 · Alembic · Pydantic v2 · JWT (access + httpOnly refresh-cookie) · pytest

## Структура

```
backend/
├── app/
│   ├── main.py              # FastAPI(), CORS, api_router, /health
│   ├── api/                 # auth, platform/, council/, admin/        → api/README.md
│   ├── core/                # config, database, security, finance (сальдо), plans (лимиты), codes
│   ├── deps/                # auth.py, fund.py (FundContext, require_fund_*), services.py
│   ├── enums/               # роли и статусы членства, валюты, тарифы, категории
│   ├── models/              # SQLAlchemy-модели
│   ├── schemas/             # Pydantic *In / *Out                     → schemas/README.md
│   ├── repositories/        # доступ к данным                         → repositories/README.md
│   ├── services/            # бизнес-логика                           → services/README.md
│   └── migrations/          # Alembic
├── scripts/seed.py          # демо-данные
├── tests/unit/              # тесты сервисов, расчёта сальдо и тарифов
├── Dockerfile
└── docker-compose.yml       # db + backend
```

Слои: `api → services → repositories → models`. Роутер тонкий, вся логика и `HTTPException` — в сервисе, `commit` — в сервисе.

## Модель данных

```
users ─┬─< fund_members >─ funds ─┬─< fund_accounts (валюта)
       │                          ├─< fund_rates (тариф взноса по месяцам)
       │   (роль, статус,         ├─< payment_requisites (валюта)
       │    помещение)            ├─< contributions (валюта, реквизит)
       └─< user_auth_providers    ├─< expenses (валюта)
           (google / telegram,    ├─< target_funds (валюта цели)
            заготовка)            ├─< account_transfers ─< announcements (finance)
                                  ├─< announcements ─< comments / likes
                                  └─< plan_requests
```

## Роли в фонде

| Возможность | Житель | Ревизор | Председатель |
|---|:-:|:-:|:-:|
| Взносы, сальдо, отчёты, объявления | ✅ | ✅ | ✅ |
| Заявки на вступление, блокировка, проверка чеков | ❌ | ✅ | ✅ |
| Расходы, целевые сборы, переводы между счетами, закреп объявлений | ❌ | ✅ | ✅ |
| Базовая валюта, тариф взноса (с 1-го числа следующего месяца), валютные счета, реквизиты | ❌ | ❌ | ✅ |
| Роли, передача председательства, удаление записей, заявка на тариф | ❌ | ❌ | ✅ |

Председатель у фонда ровно один; выйти он может только после передачи прав.

## Тарифы платформы

| Тариф | Участников | Цена |
|---|---|---|
| Free | до 10 | бесплатно |
| Pro | до 100 | 199 смн / мес |
| Max | до 500 | 399 смн / мес |
| Individual | по договору | по договору |

Председатель отправляет заявку с контактом для связи (или продление текущего тарифа) → админ платформы видит председателя и администраторов фонда с контактами, подтверждает после оплаты → тариф действует N месяцев (продление добавляется к дате окончания), затем фонд возвращается на Free (участники остаются, новых принять нельзя сверх лимита).

## Запуск локально

```bash
cp .env.example .env
docker compose up -d db
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload
```

- API: http://localhost:8000/api/v1, Swagger (при `DEV_MODE=true`): http://localhost:8000/docs
- Демо-пароль у всех — `password123`: админ платформы `+79990000000`, председатель `+79161234567`, житель `+79037890123`
- Демо-фонды: `STAR2026` (Pro, TJS/RUB/USD) и `VARZOB77` (Free, заявка на Pro ждёт админа)

## Тесты и линтеры

```bash
pytest
black app tests scripts
ruff check app tests scripts
```

## Новая фича — чек-лист

1. `models/<feature>.py` (+ `fund_id`, если данные фонда) + экспорт в `models/__init__.py`
2. миграция в `migrations/versions/`
3. `schemas/<feature>.py` (`*In` / `*Out`)
4. `repositories/<feature>_repo.py` (фильтр по `fund_id`)
5. `services/<feature>_service.py`
6. фабрика в `deps/services.py`
7. `api/<domain>/<feature>.py` (`get_fund_context` / `require_fund_*`) + подключение в `api/router.py`
8. тесты в `tests/unit/`
9. обновить README слоёв

# api — HTTP-слой

Роутеры тонкие: принимают параметры, берут контекст (`user` / `ctx`) и `service` через `Depends`, вызывают **один** метод сервиса и возвращают результат. Никакого SQL и бизнес-логики.

## Домены

| Папка | Префикс | Кто | Доступ |
|---|---|---|---|
| `auth.py` | `/api/v1/auth` | все | регистрация, вход, refresh-cookie, dev-login |
| `platform/` | `/api/v1/funds/...` | пользователи и участники фондов | `get_current_user`, `get_fund_context` |
| `council/` | `/api/v1/council/funds/{fund_id}/...` | совет фонда | `require_fund_council`, `require_fund_chairman` |
| `admin/` | `/api/v1/admin/...` | админ платформы | `require_platform_admin` |

Роль в фонде **не** лежит в JWT: `deps/fund.py` на каждый запрос проверяет активное членство в `fund_members` и отдаёт `FundContext(fund_id, user_id, member_id, role)`.

## Правила

- `router = APIRouter(prefix="/<feature>", tags=["<Domain> • <Feature>"])`
- `response_model=` указан всегда; создание → `201`, без тела → `204`
- коллекции со слешем на конце (`"/"`), действия — глаголом: `/{id}/approve`, `/{id}/toggle`, `/{id}/join`
- пагинация: `skip: int = 0, limit: int = Query(50, ge=1, le=100)`
- аргументы в сервис — именованные: `service.approve(fund_id=ctx.fund_id, member_id=member_id, reviewer_id=ctx.user_id)`
- новый роутер подключается в `router.py` в свою секцию

## Эндпоинты

### Auth

| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/register` | Регистрация (имя, телефон и/или email, пароль) |
| POST | `/auth/login` | Вход по телефону или email |
| POST | `/auth/refresh` | Новый access-токен по refresh-cookie |
| POST | `/auth/logout` | Удаляет refresh-cookie |
| GET | `/auth/me` | Текущий пользователь |
| GET / POST | `/auth/dev-users`, `/auth/dev-login` | Быстрый вход (только `DEV_MODE`) |

### Platform — фонды и вступление

| Метод | Путь | Описание |
|---|---|---|
| POST | `/funds/` | Создать фонд (создатель — председатель, базовый счёт создаётся сразу) |
| GET | `/funds/my` | Мои фонды и заявки со статусами |
| GET | `/funds/search?q=` | Поиск по коду или названию |
| GET | `/funds/by-code/{code}` | Фонд по коду / ссылке-приглашению |
| GET | `/funds/plans` | Каталог тарифов |
| POST / DELETE | `/funds/{id}/join` | Подать / отменить заявку на вступление |
| GET | `/funds/{id}` | Карточка фонда: счета с остатками, тариф, моя роль |
| POST | `/funds/{id}/leave` | Выйти из фонда (председателю — 409) |

### Platform — внутри фонда (`/funds/{fund_id}/...`, нужен активный участник)

| Метод | Путь | Описание |
|---|---|---|
| GET | `/summary` | Остатки по валютам, месяц, должники |
| GET | `/operations?type=all\|income\|expense\|transfer` | Лента операций |
| GET | `/accounts`, `/requisites` | Активные счета и реквизиты |
| GET | `/contributions/my`, `/contributions/my/balance` | Мои взносы и сальдо (в базовой валюте) |
| POST | `/contributions/` | Взнос: `requisite_id` задаёт валюту |
| GET | `/target-funds/`, `/target-funds/{id}` | Целевые сборы |
| GET | `/expenses/` | Реестр расходов |
| GET / POST / DELETE | `/announcements/...` | Доска объявлений, лайки, комментарии |
| GET | `/reports/financial?currency=`, `/reports/debtors`, `/reports/export/*` | Отчёты и CSV |

### Council (`/council/funds/{fund_id}/...`, ⭐ — только председатель)

| Метод | Путь | Описание |
|---|---|---|
| GET | `/members/?status=&only_debtors=` | Заявки и участники с сальдо |
| POST | `/members/{id}/approve`, `/reject` | Решение по заявке (лимит тарифа → 409) |
| PATCH | `/members/{id}/status` | Блокировка / разблокировка |
| PATCH ⭐ | `/members/{id}/role` | Житель ↔ ревизор |
| POST ⭐ | `/members/transfer-chairman` | Передать права председателя |
| GET / POST | `/contributions/`, `/{id}/approve`, `/{id}/reject` | Проверка чеков |
| POST / DELETE ⭐ | `/expenses/` | Расходы (валюта счёта списания) |
| POST / PATCH / toggle / DELETE ⭐ | `/target-funds/...` | Целевые сборы (валюта цели) |
| PATCH | `/settings` | Инфо фонда; ⭐ базовая валюта, тариф взноса, период |
| POST ⭐ | `/accounts`, `/accounts/{currency}/disable` | Включить / отключить валютный счёт |
| GET / POST ⭐ / toggle ⭐ / DELETE ⭐ | `/requisites` | Реквизиты с валютой |
| GET / POST | `/transfers/` | Переводы и корректировки (+ объявление) |
| GET / POST ⭐ | `/plan-requests/` | Заявки на тариф |

### Admin — админ платформы

| Метод | Путь | Описание |
|---|---|---|
| GET | `/admin/plan-requests?status=` | Заявки на тарифы |
| POST | `/admin/plan-requests/{id}/approve`, `/reject` | Включить тариф на N месяцев / отклонить |
| GET | `/admin/funds` | Все фонды с тарифами |
| PUT | `/admin/funds/{id}/plan` | Установить тариф вручную |

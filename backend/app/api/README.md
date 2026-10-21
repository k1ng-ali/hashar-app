# api — HTTP-слой

Роутеры тонкие: принимают параметры, берут контекст (`user` / `ctx`) и `service` через `Depends`, вызывают **один** метод сервиса и возвращают результат. Никакого SQL и бизнес-логики.

## Домены

| Папка | Префикс | Кто | Доступ |
|---|---|---|---|
| `auth.py` | `/api/v1/auth` | все | регистрация, вход, refresh-cookie, удаление аккаунта, dev-login |
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
| POST | `/auth/register` | Регистрация (имя, телефон и/или email, пароль); 10 в час с одного IP |
| POST | `/auth/login` | Вход по телефону или email; после 10 неудач на логин (50 на IP) за 15 мин — 429 |
| POST | `/auth/refresh` | Новый access-токен по живой сессии из refresh-cookie (срок сессии продлевается) |
| POST | `/auth/logout` | Отзывает сессию и удаляет refresh-cookie |
| POST | `/auth/logout-all` | Выход на всех устройствах (отзывает все сессии) |
| GET | `/auth/me` | Текущий пользователь |
| POST | `/auth/delete-account` | Удаление аккаунта с обезличиванием (подтверждение паролем; 403 — неверный пароль, 409 — председатель с участниками) |
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
| POST | `/contributions/` | Взнос: `requisite_id` задаёт валюту; `credited_amount` — если валюта не совпадает с валютой назначения |
| POST | `/uploads/receipt` | Загрузка фото файлом (multipart `file`, PNG / JPEG / WebP до 1,5 МБ) → `{key}`; ключ передаётся в `receipt_image` взноса, `receipt_images` расхода (до 3) или `image` сбора |
| GET | `/target-funds/`, `/target-funds/{id}` | Целевые сборы |
| GET | `/expenses/?category=&currency=`, `/expenses/{id}` | Лента расходов и карточка расхода |
| GET / POST / DELETE | `/announcements/...` | Доска объявлений, лайки, комментарии |
| GET | `/reports/financial?currency=`, `/reports/debtors` | Отчёты (CSV-выгрузки — только совет, см. ниже) |

### Council (`/council/funds/{fund_id}/...`, ⭐ — только председатель)

| Метод | Путь | Описание |
|---|---|---|
| GET | `/members/?status=&only_debtors=` | Заявки и участники с сальдо |
| POST | `/members/{id}/approve`, `/reject` | Решение по заявке (лимит тарифа → 409) |
| PATCH | `/members/{id}/status` | Блокировка / разблокировка |
| PATCH ⭐ | `/members/{id}/role` | Житель ↔ ревизор |
| POST ⭐ | `/members/transfer-chairman` | Передать права председателя |
| GET / POST | `/contributions/`, `/{id}/approve`, `/{id}/reject` | Проверка чеков (при одобрении можно поправить `credited_amount`); свой чек одобряет другой член совета |
| GET | `/contributions/history?status=&currency=&requisite_id=&q=` | История чеков с итогами по валютам |
| POST / DELETE ⭐ | `/expenses/` | Расходы (валюта счёта списания); сверх остатка — только с `allow_overdraft`; DELETE — отмена (запись остаётся) |
| POST / PATCH / toggle / DELETE ⭐ | `/target-funds/...` | Целевые сборы (валюта цели, необязательное фото `image`; в PATCH `image: null` убирает фото, валюту менять нельзя, правки пишутся в журнал); удалить можно только сбор без взносов и расходов (`has_operations: false` в карточке сбора) |
| PATCH | `/settings` | Инфо фонда; ⭐ тариф взноса (с 1-го числа следующего месяца); ⭐ базовая валюта и начало расчётов — только до первого ежемесячного взноса |
| POST ⭐ | `/accounts`, `/accounts/{currency}/disable` | Включить / отключить валютный счёт |
| GET / POST ⭐ / toggle ⭐ / DELETE ⭐ | `/requisites` | Реквизиты с валютой |
| GET / POST | `/transfers/` | Переводы и корректировки (+ объявление); списание сверх остатка — только с `allow_overdraft` |
| GET / POST ⭐ | `/plan-requests/` | Заявки на тариф и продление (обязателен `contact`) |
| GET | `/audit/` | Журнал действий совета и админа платформы |
| GET | `/notices/` | Уведомления от платформы: сообщения админа, решения по заявкам на тариф, окончание тарифа; `unread` — непрочитанные |
| POST | `/notices/read` | Отметить уведомления прочитанными (по `fund_members.notices_read_at`) |
| GET | `/reports/export/contributions`, `/expenses`, `/debtors` | CSV-реестры (имена, помещения, телефоны) |

### Admin — админ платформы

| Метод | Путь | Описание |
|---|---|---|
| GET | `/admin/plan-requests?status=` | Заявки на тарифы |
| POST | `/admin/plan-requests/{id}/approve`, `/reject` | Включить тариф на N месяцев / отклонить; для individual обязательна `monthly_price`; остаток прежнего тарифа переносится в дни нового |
| GET | `/admin/funds` | Все фонды с тарифами, председателем и администраторами (контакты) |
| PUT | `/admin/funds/{id}/plan` | Установить тариф вручную |
| GET | `/admin/analytics/overview?months=` | Сводка платформы: пользователи и фонды (всего, новые и активные за 30 дней), подтверждение личности, рост по месяцам, взносы и расходы по валютам |
| GET | `/admin/analytics/plans?months=` | Распределение по действующим тарифам, выручка по месяцам (из `plan.approve` в журнале: цена × месяцы), MRR, заявки, тарифы, истекающие за 14 дней |
| GET | `/admin/analytics/funds?q=&plan=&inactive=&sort=` | Фонды со счётчиками: участники, заявки, чеки (и ждущие дольше 3 дней), последняя активность; `sort` — created / members / activity / pending |
| GET | `/admin/users?q=&filter=` | Пользователи (поиск по имени, телефону, email; `filter` — all / unverified / admins / deleted) — только просмотр |
| GET | `/admin/users/{id}` | Пользователь: фонды и роли, активные сессии |
| GET | `/admin/audit?fund_id=&actor_id=&entity=` | Журнал действий всей платформы с названием фонда |
| POST | `/admin/funds/{id}/notices` | Уведомление совету фонда от админа платформы (пишется в журнал `notice.send`) |
| GET | `/admin/notices?fund_id=` | Отправленные уведомления |

# services — бизнес-логика

Один сервис = один домен. Класс `<Feature>Service(db: AsyncSession)` держит `self.db` и свои репозитории.

## Правила

- вся бизнес-логика и проверки (членство, роли, статусы, валюты, лимиты) — здесь
- `HTTPException` выбрасывается прямо в сервисе: 404 — не найдено, 403 — нет прав, 409 — конфликт состояния
- `commit()` делает сервис, репозиторий — только `flush()`
- все доменные запросы ограничены `fund_id` — чужой фонд недоступен даже по прямому id
- конкурентные изменения — `get(..., for_update=True)`
- ORM → схема: модульные функции `contribution_out()`, `member_out()`, `transfer_out()` и т.п.
- фабрика для DI — в `app/deps/services.py`

## Структура и методы

| Сервис | Методы | Правила |
|---|---|---|
| `AuthService` | `register`, `login`, `refresh`, `me`, `dev_login`, `list_demo_users` | Логин — телефон (нормализуется) или email |
| `FundService` | `create`, `search`, `get_by_code`, `join`, `cancel_request`, `leave`, `list_my`, `get`, `update` | Создатель — председатель; председатель не может выйти; финансовые настройки — только председатель |
| `MemberService` | `list_members`, `approve`, `reject`, `set_status`, `set_role`, `transfer_chairman`, `get_balance`, `list_debtors` | Лимит тарифа при одобрении; председателя и себя менять нельзя |
| `PlanService` | `catalog`, `info`, `ensure_capacity`, `create_request`, `list_requests`, `approve`, `reject`, `list_funds`, `set_plan` | Одна заявка в ожидании; продление — от текущей даты окончания |
| `AccountService` | `balances`, `list_accounts`, `enable_currency`, `disable_currency`, реквизиты, `create_transfer` | Базовый счёт не отключается; отключить можно только пустой счёт; перевод публикует объявление |
| `DashboardService` | `summary`, `operations` | Остатки и метрики месяца по каждой валюте |
| `ContributionService` | `list_my`, `create`, `list_all`, `approve`, `reject` | Валюта = валюта реквизита; ежемесячный взнос — только в базовой валюте; в сбор — только в валюте сбора |
| `ExpenseService` | `list`, `create`, `delete` | Расход со счёта включённой валюты |
| `TargetFundService` | `list`, `get_detail`, `create`, `update`, `toggle`, `delete` | У сбора своя валюта |
| `AnnouncementService` | `list`, `create`, `toggle_like`, `add_comment`, `delete` | Закреп — совет; объявления о переводах не удаляются |
| `ReportService` | `financial(currency)`, `debtors`, `export_*` | Отчёт по одному валютному счёту; CSV с колонкой валюты |

## Деньги и валюты

- у фонда счёт на каждую включённую валюту (`fund_accounts`); остаток не хранится:
  `взносы (approved) − расходы + зачисления − списания` по каждой валюте
- курсы платформа не считает: при переводе совет вводит обе суммы
- сальдо участника (`core/finance.py`) — только в базовой валюте фонда:
  начислено = тариф × месяцев с `max(start_period фонда, месяц вступления)` по текущий
- тарифы платформы (`core/plans.py`): Free — 10, Pro — 100, Max — 500, Individual — лимит от админа;
  после `plan_expires_at` действует Free

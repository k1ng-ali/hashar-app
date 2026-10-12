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
| `ContributionService` | `list_my`, `create`, `list_all`, `history`, `approve`, `reject` | Валюта = валюта реквизита (любого активного); зачёт — в базовой валюте или валюте сбора, при оплате в другой валюте сумму зачёта вводит участник, совет может поправить при одобрении; снимок реквизита в `requisite_label` |
| `ExpenseService` | `list(category, currency)`, `get`, `create`, `delete` | Расход со счёта включённой валюты; сверх остатка — 409, если не подтверждён `allow_overdraft` (`AccountService.ensure_sufficient`, с блокировкой строки фонда) |
| `TargetFundService` | `list`, `get_detail`, `create`, `update`, `toggle`, `delete` | У сбора своя валюта |
| `AnnouncementService` | `list`, `create`, `toggle_like`, `add_comment`, `delete` | Закреп — совет; объявления о переводах не удаляются |
| `ReportService` | `financial(currency)`, `debtors`, `export_*` | Отчёт по одному валютному счёту; CSV с колонкой валюты |

## Деньги и валюты

- у фонда счёт на каждую включённую валюту (`fund_accounts`); остаток не хранится:
  `взносы (approved) − расходы + зачисления − списания` по каждой валюте
- курсы платформа не считает: при переводе совет вводит обе суммы
- сальдо участника (`core/finance.py`) — только в базовой валюте фонда:
  начислено = сумма тарифов каждого месяца с `max(start_period фонда, месяц вступления)` по текущий;
  оплачено = зачтённые суммы (`credited_amount`) одобренных ежемесячных взносов
- выход не удаляет участника: статус `left`, долг за время участия остаётся; сальдо отсутствующего
  (вышел / заблокирован) замирает на месяце ухода. При возвращении (`approve`) и разблокировке
  (`set_status`) совет обязан передать `accrue_absence`: «без начисления» создаёт паузу
  (`member_accrual_pauses`) на месяцы строго между уходом и текущим. Вышедший во время блокировки
  разблокируется без выбора (→ `left`), решение — при его заявке на возвращение
- тариф взноса хранится историей (`fund_rates`): месяц начисляется по тарифу, действовавшему в нём;
  смена тарифа вступает в силу с 1-го числа следующего месяца (`FundService._schedule_rate`)
- тарифы платформы (`core/plans.py`): Free — 10, Pro — 100, Max — 500, Individual — лимит от админа;
  после `plan_expires_at` действует Free; продление того же тарифа добавляет месяцы к текущей дате окончания

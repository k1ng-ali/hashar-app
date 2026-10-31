# repositories — доступ к данным

Наследуют `BaseRepository(db)`. Только запросы (`select / update / delete / func`), без бизнес-логики и HTTP-ошибок.

## Правила

- `add` + `flush` (+ `refresh` или перечитывание со связями), **без** `commit`
- доменные методы принимают `fund_id` первым аргументом и всегда фильтруют по нему
- связи у моделей `lazy="raise"` — всё, что нужно для ответа, грузим явно через `selectinload`
- при перечитывании объекта из сессии — `execution_options(populate_existing=True)`
- агрегаты возвращают простые `dict` / `tuple` (обычно `{currency: сумма}`)
- поиск по подстроке — `like_pattern()` из `base_repo.py` + `ilike(..., escape="\\")`: `%` и `_` пользователя не шаблон
- в модуле с методом `list()` — `from __future__ import annotations`: на Python 3.12 метод затеняет `list[...]` в аннотациях ниже

## Структура и методы

| Файл | Методы |
|---|---|
| `base_repo.py` | `BaseRepository(db)`, `like_pattern` |
| `auth_session_repo.py` | `get(for_update)`, `create`, `revoke_all`, `delete_all` |
| `audit_repo.py` | `add` (без flush — уходит с commit сервиса), `list` |
| `user_repo.py` | `get(for_update)`, `get_by_login`, `exists_login`, `list_all` (без удалённых), `create`, `delete_auth_providers` |
| `fund_repo.py` | `get(for_update)`, `get_by_code`, `code_exists`, `search`, `list_all`, `create`, `list_accounts`, `get_account`, `create_account` |
| `member_repo.py` | `get(for_update)`, `get_by_user`, `get_chairman`, `list(status)`, `list_council_by_funds`, `list_by_user`, `first_council_user_ids`, `count_active`, `count_active_by_funds`, `has_other_council`, `units_by_users`, `create` |
| `pricing_repo.py` | `list_prices`, `get_price(for_update)`, `list_discounts`, `list_running_sales`, `get_discount(for_update)`, `get_by_code(for_update)`, `count_uses(fund_id)`, `uses_by_discount`, `create_discount`, `delete_discount` |
| `plan_request_repo.py` | `get(for_update)`, `list(status, fund_id)`, `has_pending`, `replace_contact`, `create` |
| `requisite_repo.py` | `get`, `list(active_only, currencies)`, `create`, `delete` |
| `transfer_repo.py` | `get`, `list`, `sums_by_currency` → `(зачислено, списано)`, `create` |
| `fund_rate_repo.py` | `list`, `schedule` → `[(период, тариф)]`, `get`, `create`, `delete` |
| `contribution_repo.py` | `get(for_update)`, `list(ContributionFilters)`, `totals(ContributionFilters)`, `monthly_sums_by_user(currency)`, `approved_sums_by_currency`, `has_monthly_fees`, `exists_for_target_fund`, `count_pending`, `collected_by_target_funds`, `approved_monthly_sums`, `create` |
| `expense_repo.py` | `get`, `list`, `sums_by_currency`, `sums_by_category(currency)`, `monthly_sums(currency)`, `create`, `exists_for_target_fund` — все без отменённых (`deleted_at`) |
| `target_fund_repo.py` | `get(for_update)`, `list(active_only)`, `create`, `delete` |
| `announcement_repo.py` | `get`, `list`, `create`, `delete`, `create_comment`, `likes_count`, `liked_ids`, `add_like`, `remove_like` |
| `analytics_repo.py` | агрегаты платформы: `count_*`, `verification_stats`, `new_*_by_month`, `*_by_month` / `*_by_currency`, `plan_distribution`, `mrr`, `revenue_*`, `expiring_funds`, `list_fund_health`, `list_users`, `get_user_row`, `list_memberships`, `count_active_sessions`, `list_audit` |
| `notice_repo.py` | `add` (без flush), `add_once(dedupe_key)` (ON CONFLICT DO NOTHING), `list`, `count_since`, `list_all`, `list_funds_by_expiry` |

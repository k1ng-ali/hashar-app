# repositories — доступ к данным

Наследуют `BaseRepository(db)`. Только запросы (`select / update / delete / func`), без бизнес-логики и HTTP-ошибок.

## Правила

- `add` + `flush` (+ `refresh` или перечитывание со связями), **без** `commit`
- доменные методы принимают `fund_id` первым аргументом и всегда фильтруют по нему
- связи у моделей `lazy="raise"` — всё, что нужно для ответа, грузим явно через `selectinload`
- при перечитывании объекта из сессии — `execution_options(populate_existing=True)`
- агрегаты возвращают простые `dict` / `tuple` (обычно `{currency: сумма}`)

## Структура и методы

| Файл | Методы |
|---|---|
| `base_repo.py` | `BaseRepository(db)` |
| `user_repo.py` | `get`, `get_by_login`, `exists_login`, `list_all`, `create` |
| `fund_repo.py` | `get(for_update)`, `get_by_code`, `code_exists`, `search`, `list_all`, `create`, `list_accounts`, `get_account`, `create_account` |
| `member_repo.py` | `get(for_update)`, `get_by_user`, `get_chairman`, `list(status)`, `list_council_by_funds`, `list_by_user`, `count_active`, `count_active_by_funds`, `units_by_users`, `create` |
| `plan_request_repo.py` | `get(for_update)`, `list(status, fund_id)`, `has_pending`, `create` |
| `requisite_repo.py` | `get`, `list(active_only, currencies)`, `create`, `delete` |
| `transfer_repo.py` | `get`, `list`, `sums_by_currency` → `(зачислено, списано)`, `create` |
| `fund_rate_repo.py` | `list`, `schedule` → `[(период, тариф)]`, `get`, `create`, `delete` |
| `contribution_repo.py` | `get(for_update)`, `list(ContributionFilters)`, `totals(ContributionFilters)`, `monthly_sums_by_user(currency)`, `approved_sums_by_currency`, `count_pending`, `collected_by_target_funds`, `approved_monthly_sums`, `create` |
| `expense_repo.py` | `get`, `list`, `sums_by_currency`, `sums_by_category(currency)`, `monthly_sums(currency)`, `create`, `delete` |
| `target_fund_repo.py` | `get(for_update)`, `list(active_only)`, `create`, `delete` |
| `announcement_repo.py` | `get`, `list`, `create`, `delete`, `create_comment`, `likes_count`, `liked_ids`, `add_like`, `remove_like` |

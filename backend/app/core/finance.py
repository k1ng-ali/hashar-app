"""
Расчёт сальдо жителя и работа с расчётными периодами (YYYY-MM).

Чистые функции без БД — их удобно покрывать unit-тестами.

Правила:
- начисление: сумма тарифов за каждый месяц от начала расчётов до текущего включительно;
  тариф месяца берётся из истории (fund_rates), поэтому смена тарифа прошлое не меняет
- оплата закрывает месяцы по порядку: май по тарифу мая, июнь по тарифу июня и т. д.
- оплачено: зачтённые суммы (credited_amount) одобренных ежемесячных взносов в базовой валюте фонда
- чеки на проверке (pending) показываются отдельно и в сальдо не входят
- excluded — месяцы паузы (совет решил не начислять за отсутствие / блокировку):
  в них ничего не начисляется, и оплата их пропускает
"""

from datetime import datetime, timezone

from app.enums import BalanceStatusEnum
from app.schemas.balance import ResidentBalanceOut

# [(период "YYYY-MM", тариф)] по возрастанию периода; запись действует до следующей
RateSchedule = list[tuple[str, int]]

# Предохранитель: дальше 100 лет вперёд аванс не раскладываем
MAX_COVERED_MONTHS = 1200


def current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def period_of(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def shift_period(period: str, months: int) -> str:
    year, month = map(int, period.split("-"))
    index = year * 12 + (month - 1) + months
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def periods_range(start: str, end: str) -> list[str]:
    """Все периоды от start до end включительно. Пустой список, если start > end."""
    result = []
    period = start
    while period <= end:
        result.append(period)
        period = shift_period(period, 1)
    return result


def rate_at(schedule: RateSchedule, period: str) -> int:
    """Тариф, действующий в месяце period. До первой записи — тариф первой записи."""
    if not schedule:
        return 0
    amount = schedule[0][1]
    for start, value in schedule:
        if start > period:
            break
        amount = value
    return amount


def next_rate_change(schedule: RateSchedule, period: str) -> tuple[str, int] | None:
    """Ближайшее запланированное изменение тарифа после месяца period."""
    for start, value in schedule:
        if start > period:
            return start, value
    return None


def calculate_balance(
    paid: int,
    pending: int,
    schedule: RateSchedule,
    start_period: str,
    today_period: str,
    currency: str = "tjs",
    excluded: frozenset[str] | set[str] = frozenset(),
) -> ResidentBalanceOut:
    accrued = [period for period in periods_range(start_period, today_period) if period not in excluded]
    total_due = sum(rate_at(schedule, period) for period in accrued)
    balance = paid - total_due

    # Оплата закрывает месяцы по порядку, каждый — по своему тарифу
    covered: list[str] = []
    remaining = paid
    period = start_period
    for _ in range(MAX_COVERED_MONTHS):
        if period in excluded:
            period = shift_period(period, 1)
            continue
        rate = rate_at(schedule, period)
        if rate == 0:
            # Бесплатный месяц закрыт сам собой, но вперёд за него не «платим»
            if period > today_period:
                break
        elif remaining < rate:
            break
        remaining -= rate
        covered.append(period)
        period = shift_period(period, 1)

    covered_set = set(covered)
    unpaid = [p for p in accrued if p not in covered_set]

    debt_amount = -balance if balance < 0 else 0
    advance_amount = balance if balance > 0 else 0

    if balance < 0:
        status = BalanceStatusEnum.debt
    elif balance > 0:
        status = BalanceStatusEnum.advance
    else:
        status = BalanceStatusEnum.ok

    next_period = shift_period(today_period, 1)
    return ResidentBalanceOut(
        status=status,
        currency=currency,
        rate=rate_at(schedule, today_period),
        next_rate=rate_at(schedule, next_period),
        balance=balance,
        total_due=total_due,
        total_paid=paid,
        pending_amount=pending,
        has_pending=pending > 0,
        paid_months_count=len(covered),
        paid_until_period=covered[-1] if covered else None,
        debt_amount=debt_amount,
        # Неполностью оплаченный месяц тоже считается долгом
        debt_months_count=len(unpaid),
        advance_amount=advance_amount,
        advance_months_count=sum(1 for p in covered if p > today_period),
        covered_periods=covered,
        unpaid_periods=unpaid,
        current_period=today_period,
        next_billing_period=next_period,
    )

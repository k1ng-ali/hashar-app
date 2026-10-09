"""
Расчёт сальдо жителя и работа с расчётными периодами (YYYY-MM).

Чистые функции без БД — их удобно покрывать unit-тестами.

Правила:
- начисление: тариф × количество месяцев от start_period фонда до текущего включительно
- оплачено: только одобренные (approved) ежемесячные взносы в базовой валюте фонда
- чеки на проверке (pending) показываются отдельно и в сальдо не входят
"""

from datetime import datetime, timezone

from app.enums import BalanceStatusEnum
from app.schemas.balance import ResidentBalanceOut


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


def calculate_balance(
    paid: int,
    pending: int,
    rate: int,
    start_period: str,
    today_period: str,
    currency: str = "tjs",
) -> ResidentBalanceOut:
    accrued = periods_range(start_period, today_period)
    total_due = len(accrued) * rate
    balance = paid - total_due

    paid_months_count = paid // rate if rate > 0 else 0
    covered = [shift_period(start_period, i) for i in range(paid_months_count)]
    unpaid = [p for p in accrued if p not in covered]

    debt_amount = -balance if balance < 0 else 0
    advance_amount = balance if balance > 0 else 0

    if balance < 0:
        status = BalanceStatusEnum.debt
    elif balance > 0:
        status = BalanceStatusEnum.advance
    else:
        status = BalanceStatusEnum.ok

    return ResidentBalanceOut(
        status=status,
        currency=currency,
        rate=rate,
        balance=balance,
        total_due=total_due,
        total_paid=paid,
        pending_amount=pending,
        has_pending=pending > 0,
        paid_months_count=paid_months_count,
        paid_until_period=covered[-1] if covered else None,
        debt_amount=debt_amount,
        # Округление вверх: неполный месяц тоже считается долгом
        debt_months_count=-(-debt_amount // rate) if rate > 0 else 0,
        advance_amount=advance_amount,
        advance_months_count=advance_amount // rate if rate > 0 else 0,
        covered_periods=covered,
        unpaid_periods=unpaid,
        current_period=today_period,
        next_billing_period=shift_period(today_period, 1),
    )

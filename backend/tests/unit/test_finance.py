from app.core.finance import calculate_balance, periods_range, rate_at, shift_period
from app.enums import BalanceStatusEnum


def test_shift_period_across_year():
    assert shift_period("2026-12", 1) == "2027-01"
    assert shift_period("2026-01", -1) == "2025-12"


def test_periods_range_inclusive():
    assert periods_range("2026-07", "2026-09") == ["2026-07", "2026-08", "2026-09"]
    assert periods_range("2026-10", "2026-09") == []


def test_calculate_balance_debt():
    balance = calculate_balance(
        paid=3000, pending=0, schedule=[("2026-07", 1500)], start_period="2026-07", today_period="2026-10"
    )

    assert balance.status == BalanceStatusEnum.debt
    assert balance.total_due == 6000
    assert balance.debt_amount == 3000
    assert balance.debt_months_count == 2
    assert balance.covered_periods == ["2026-07", "2026-08"]
    assert balance.unpaid_periods == ["2026-09", "2026-10"]
    assert balance.next_billing_period == "2026-11"


def test_calculate_balance_partial_month_counts_as_debt_month():
    balance = calculate_balance(
        paid=2250, pending=0, schedule=[("2026-07", 1500)], start_period="2026-07", today_period="2026-08"
    )

    assert balance.debt_amount == 750
    assert balance.debt_months_count == 1


def test_calculate_balance_advance():
    balance = calculate_balance(
        paid=9000, pending=0, schedule=[("2026-07", 1500)], start_period="2026-07", today_period="2026-09"
    )

    assert balance.status == BalanceStatusEnum.advance
    assert balance.advance_amount == 4500
    assert balance.advance_months_count == 3
    assert balance.paid_until_period == "2026-12"
    assert balance.unpaid_periods == []


def test_calculate_balance_ok_with_pending():
    balance = calculate_balance(
        paid=1500,
        pending=1500,
        schedule=[("2026-09", 1500)],
        start_period="2026-09",
        today_period="2026-09",
        currency="rub",
    )

    assert balance.status == BalanceStatusEnum.ok
    assert balance.currency == "rub"
    assert balance.has_pending is True
    assert balance.pending_amount == 1500


def test_rate_at_uses_latest_record_before_period():
    schedule = [("2026-05", 50), ("2026-06", 100)]
    assert rate_at(schedule, "2026-04") == 50  # до первой записи — первый тариф
    assert rate_at(schedule, "2026-05") == 50
    assert rate_at(schedule, "2026-09") == 100
    assert rate_at([], "2026-09") == 0


def test_rate_change_does_not_rewrite_past_months():
    # Май — 50, с июня — 100: за май 50, за июнь и июль по 100
    schedule = [("2026-05", 50), ("2026-06", 100)]
    balance = calculate_balance(paid=150, pending=0, schedule=schedule, start_period="2026-05", today_period="2026-07")

    assert balance.total_due == 250
    assert balance.debt_amount == 100
    assert balance.covered_periods == ["2026-05", "2026-06"]
    assert balance.unpaid_periods == ["2026-07"]
    assert balance.rate == 100


def test_advance_is_spread_by_future_rate():
    # Повышение с сентября запланировано: аванс за сентябрь закрывается по новому тарифу
    schedule = [("2026-07", 100), ("2026-09", 200)]
    balance = calculate_balance(paid=400, pending=0, schedule=schedule, start_period="2026-07", today_period="2026-08")

    assert balance.covered_periods == ["2026-07", "2026-08", "2026-09"]
    assert balance.advance_months_count == 1
    assert balance.next_rate == 200

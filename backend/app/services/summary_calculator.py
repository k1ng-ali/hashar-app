from sqlalchemy.orm import Session
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.models.contribution import Contribution, ContributionStatus, ContributionCategory
from backend.app.models.expense import Expense
from backend.app.models.rate import BillingRate
from backend.app.schemas.summary import ResidentBalanceStatusResponse, FundSummaryResponse

CURRENT_PERIOD = "2026-09"
ACCRUED_PERIODS = ["2026-07", "2026-08", "2026-09"]
BASE_PERIODS = [
    "2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12",
    "2027-01", "2027-02", "2027-03", "2027-04", "2027-05", "2027-06",
]


def calculate_resident_status(user: User, db: Session) -> ResidentBalanceStatusResponse:
    rate_obj = db.query(BillingRate).order_by(BillingRate.id.desc()).first()
    rate = rate_obj.amount if rate_obj and rate_obj.amount > 0 else 1500

    total_due = len(ACCRUED_PERIODS) * rate  # 4500 ₽

    monthly_contributions = (
        db.query(Contribution)
        .filter(
            Contribution.user_id == user.id,
            Contribution.category == ContributionCategory.MONTHLY_FEE,
        )
        .all()
    )

    approved_paid = sum(c.amount for c in monthly_contributions if c.status == ContributionStatus.APPROVED)
    pending_contributions = [c for c in monthly_contributions if c.status == ContributionStatus.PENDING]
    pending_amount = sum(c.amount for c in pending_contributions)
    has_pending = len(pending_contributions) > 0

    total_paid = approved_paid + pending_amount
    balance = total_paid - total_due

    paid_months_count = total_paid // rate
    covered_periods = BASE_PERIODS[:paid_months_count]
    paid_until_period = covered_periods[-1] if covered_periods else None

    unpaid_periods = [p for p in ACCRUED_PERIODS if p not in covered_periods]

    next_billing_period = "2026-10"
    next_billing_date = "1 октября 2026 г."
    next_billing_amount = rate

    if balance < 0:
        debt_amount = abs(balance)
        debt_months_count = (debt_amount + rate - 1) // rate
        status_type = "DEBT"
        advance_months_count = 0
        advance_amount = 0
    elif balance > 0:
        advance_amount = balance
        advance_months_count = advance_amount // rate
        status_type = "ADVANCE"
        debt_months_count = 0
        debt_amount = 0
        unpaid_periods = []
        if not paid_until_period:
            paid_until_period = "2026-10"
    else:
        status_type = "OK"
        debt_months_count = 0
        debt_amount = 0
        advance_months_count = 0
        advance_amount = 0
        unpaid_periods = []
        if not paid_until_period:
            paid_until_period = "2026-09"

    return ResidentBalanceStatusResponse(
        paid_months_count=paid_months_count,
        paid_until_period=paid_until_period,
        debt_months_count=debt_months_count,
        debt_amount=debt_amount,
        advance_months_count=advance_months_count,
        advance_amount=advance_amount,
        status_type=status_type,
        balance=balance,
        total_paid=total_paid,
        total_due=total_due,
        has_pending=has_pending,
        pending_amount=pending_amount,
        next_billing_period=next_billing_period,
        next_billing_date=next_billing_date,
        next_billing_amount=next_billing_amount,
        covered_periods=covered_periods,
        unpaid_periods=unpaid_periods,
    )


def calculate_fund_summary(db: Session) -> FundSummaryResponse:
    all_contributions = db.query(Contribution).all()
    approved_contribs = [c for c in all_contributions if c.status == ContributionStatus.APPROVED]
    pending_contribs = [c for c in all_contributions if c.status == ContributionStatus.PENDING]

    expenses = db.query(Expense).all()

    total_collected = sum(c.amount for c in approved_contribs)
    total_expenses = sum(e.amount for e in expenses)
    total_balance = total_collected - total_expenses

    # Current month (2026-09)
    current_month_approved = [
        c for c in approved_contribs
        if str(c.created_at).startswith(CURRENT_PERIOD) or c.billing_period == CURRENT_PERIOD
    ]
    current_month_collected = sum(c.amount for c in current_month_approved)

    current_month_spent = sum(
        e.amount for e in expenses if str(e.created_at).startswith(CURRENT_PERIOD)
    )

    pending_contributions_count = len(pending_contribs)
    pending_contributions_amount = sum(c.amount for c in pending_contribs)

    active_residents = (
        db.query(User)
        .filter(User.role == UserRole.RESIDENT, User.status == UserStatus.ACTIVE)
        .all()
    )

    debtors_count = 0
    for resident in active_residents:
        stat = calculate_resident_status(resident, db)
        if stat.status_type == "DEBT":
            debtors_count += 1

    return FundSummaryResponse(
        total_balance=total_balance,
        total_collected=total_collected,
        total_expenses=total_expenses,
        current_month_collected=current_month_collected,
        current_month_spent=current_month_spent,
        pending_contributions_count=pending_contributions_count,
        pending_contributions_amount=pending_contributions_amount,
        active_residents_count=len(active_residents),
        debtors_count=debtors_count,
    )

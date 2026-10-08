import io
import csv
from datetime import datetime
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.contribution import Contribution, ContributionStatus
from backend.app.models.expense import Expense
from backend.app.schemas.summary import FundSummaryResponse, ResidentBalanceStatusResponse
from backend.app.schemas.report import FinancialReportResponse, MonthlyLedgerRow, CategoryStat
from backend.app.services.summary_calculator import (
    calculate_fund_summary,
    calculate_resident_status,
)

router = APIRouter()


@router.get("/summary", response_model=FundSummaryResponse)
def get_summary(db: Session = Depends(get_db)):
    return calculate_fund_summary(db)


@router.get("/financial", response_model=FinancialReportResponse)
def get_financial_report(db: Session = Depends(get_db)):
    approved = (
        db.query(Contribution)
        .filter(Contribution.status == ContributionStatus.APPROVED)
        .all()
    )
    expenses = db.query(Expense).all()

    periods = [
        ("2026-09", "Сентябрь 2026", True),
        ("2026-08", "Август 2026", False),
        ("2026-07", "Июль 2026", False),
    ]

    monthly_rows = []
    for code, title, is_curr in periods:
        inc = sum(c.amount for c in approved if str(c.created_at).startswith(code))
        exp = sum(e.amount for e in expenses if str(e.created_at).startswith(code))
        monthly_rows.append(
            MonthlyLedgerRow(
                period=code,
                title=title,
                income=inc,
                expense=exp,
                delta=inc - exp,
                is_current=is_curr,
            )
        )

    total_expense = sum(e.amount for e in expenses) or 1
    categories = ["Ремонт", "Электрика", "Аварийные работы", "Хознужды", "Озеленение", "Видеонаблюдение"]
    category_stats = []
    for cat in categories:
        cat_sum = sum(e.amount for e in expenses if e.category == cat)
        if cat_sum > 0:
            category_stats.append(
                CategoryStat(
                    name=cat,
                    total=cat_sum,
                    percent=round((cat_sum / total_expense) * 100),
                )
            )
    category_stats.sort(key=lambda x: x.total, reverse=True)

    total_income = sum(c.amount for c in approved)
    real_total_expense = sum(e.amount for e in expenses)

    return FinancialReportResponse(
        monthly_rows=monthly_rows,
        category_stats=category_stats,
        total_income=total_income,
        total_expense=real_total_expense,
        net_balance=total_income - real_total_expense,
    )


@router.get("/debtors", response_model=list[ResidentBalanceStatusResponse])
def get_debtors(db: Session = Depends(get_db)):
    residents = db.query(User).filter(User.role == UserRole.RESIDENT).all()
    debtors = []
    for r in residents:
        stat = calculate_resident_status(r, db)
        if stat.status_type == "DEBT":
            debtors.append(stat)
    return debtors


@router.get("/export/contributions")
def export_contributions_csv(db: Session = Depends(get_db)):
    contributions = db.query(Contribution).order_by(Contribution.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    output.write("\ufeff")  # UTF-8 BOM for Excel
    writer.writerow(["ID", "Дата", "Плательщик", "Помещение", "Категория", "Сумма", "Статус"])
    for c in contributions:
        writer.writerow([c.id, str(c.created_at), c.user_name, c.user_unit, c.category, c.amount, c.status.value])

    filename = f"reestr_vznosov_{datetime.now().strftime('%Y-%m-%d')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/expenses")
def export_expenses_csv(db: Session = Depends(get_db)):
    expenses = db.query(Expense).order_by(Expense.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    output.write("\ufeff")
    writer.writerow(["ID", "Дата", "Название", "Категория", "Сумма", "Ответственный", "Описание"])
    for e in expenses:
        writer.writerow([e.id, str(e.created_at), e.title, e.category, e.amount, e.created_by_admin_name, e.description])

    filename = f"reestr_rashodov_{datetime.now().strftime('%Y-%m-%d')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

from fastapi import APIRouter, Depends, Query

from app.deps.fund import get_fund_context
from app.deps.services import get_report_service
from app.enums import CurrencyEnum
from app.schemas.member import FundContext
from app.schemas.report import DebtorOut, FinancialReportOut
from app.services.report_service import ReportService

router = APIRouter(prefix="/funds/{fund_id}/reports", tags=["Platform • Reports"])


@router.get("/financial", response_model=FinancialReportOut)
async def get_financial_report(
    currency: CurrencyEnum | None = None,
    months: int = Query(6, ge=1, le=24),
    ctx: FundContext = Depends(get_fund_context),
    service: ReportService = Depends(get_report_service),
):
    return await service.financial(fund_id=ctx.fund_id, currency=currency, months=months)


@router.get("/debtors", response_model=list[DebtorOut])
async def list_debtors(
    ctx: FundContext = Depends(get_fund_context),
    service: ReportService = Depends(get_report_service),
):
    return await service.debtors(fund_id=ctx.fund_id)

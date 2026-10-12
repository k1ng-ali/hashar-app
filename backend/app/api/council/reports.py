from fastapi import APIRouter, Depends, Response

from app.deps.fund import require_fund_council
from app.deps.services import get_report_service
from app.schemas.member import FundContext
from app.services.report_service import ReportService

# CSV-реестры (с именами, помещениями и телефонами участников) выгружает только совет
router = APIRouter(prefix="/funds/{fund_id}/reports/export", tags=["Council • Reports"])


def _csv_response(filename: str, content: str) -> Response:
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/contributions")
async def export_contributions(
    ctx: FundContext = Depends(require_fund_council),
    service: ReportService = Depends(get_report_service),
):
    return _csv_response(*await service.export_contributions(fund_id=ctx.fund_id))


@router.get("/expenses")
async def export_expenses(
    ctx: FundContext = Depends(require_fund_council),
    service: ReportService = Depends(get_report_service),
):
    return _csv_response(*await service.export_expenses(fund_id=ctx.fund_id))


@router.get("/debtors")
async def export_debtors(
    ctx: FundContext = Depends(require_fund_council),
    service: ReportService = Depends(get_report_service),
):
    return _csv_response(*await service.export_debtors(fund_id=ctx.fund_id))

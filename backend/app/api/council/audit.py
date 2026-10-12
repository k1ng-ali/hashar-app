from fastapi import APIRouter, Depends, Query

from app.deps.fund import require_fund_council
from app.deps.services import get_audit_service
from app.schemas.audit import AuditEventOut
from app.schemas.member import FundContext
from app.services.audit_service import AuditService

router = APIRouter(prefix="/funds/{fund_id}/audit", tags=["Council • Audit"])


@router.get("/", response_model=list[AuditEventOut])
async def list_audit_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    ctx: FundContext = Depends(require_fund_council),
    service: AuditService = Depends(get_audit_service),
):
    return await service.list(fund_id=ctx.fund_id, skip=skip, limit=limit)

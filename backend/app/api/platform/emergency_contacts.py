from fastapi import APIRouter, Depends

from app.deps.fund import get_fund_context
from app.deps.services import get_emergency_contact_service
from app.schemas.emergency_contact import EmergencyContactOut
from app.schemas.member import FundContext
from app.services.emergency_contact_service import EmergencyContactService

router = APIRouter(prefix="/funds/{fund_id}/emergency-contacts", tags=["Platform • Emergency contacts"])


@router.get("/", response_model=list[EmergencyContactOut])
async def list_emergency_contacts(
    ctx: FundContext = Depends(get_fund_context),
    service: EmergencyContactService = Depends(get_emergency_contact_service),
):
    return await service.list(fund_id=ctx.fund_id)

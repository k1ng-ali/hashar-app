from fastapi import APIRouter, Depends, status

from app.deps.fund import require_fund_council
from app.deps.services import get_emergency_contact_service
from app.schemas.emergency_contact import EmergencyContactIn, EmergencyContactOut
from app.schemas.member import FundContext
from app.services.emergency_contact_service import EmergencyContactService

router = APIRouter(prefix="/funds/{fund_id}/emergency-contacts", tags=["Council • Emergency contacts"])


@router.post("/", response_model=EmergencyContactOut, status_code=status.HTTP_201_CREATED)
async def create_emergency_contact(
    payload: EmergencyContactIn,
    ctx: FundContext = Depends(require_fund_council),
    service: EmergencyContactService = Depends(get_emergency_contact_service),
):
    return await service.create(fund_id=ctx.fund_id, user_id=ctx.user_id, payload=payload)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_emergency_contact(
    contact_id: int,
    ctx: FundContext = Depends(require_fund_council),
    service: EmergencyContactService = Depends(get_emergency_contact_service),
):
    await service.delete(fund_id=ctx.fund_id, contact_id=contact_id)

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.emergency_contact_repo import EmergencyContactRepository
from app.schemas.emergency_contact import EmergencyContactIn, EmergencyContactOut

# Справочник, а не телефонная книга — длинный список никто не читает
MAX_CONTACTS = 30


class EmergencyContactService:
    """Экстренные телефоны фонда: смотрят все участники, ведёт совет."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = EmergencyContactRepository(db=db)

    async def list(self, fund_id: int) -> list[EmergencyContactOut]:
        return [EmergencyContactOut.model_validate(c) for c in await self.repo.list(fund_id)]

    async def create(self, fund_id: int, user_id: int, payload: EmergencyContactIn) -> EmergencyContactOut:
        if await self.repo.count(fund_id) >= MAX_CONTACTS:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Too many contacts")
        contact = await self.repo.create(
            fund_id=fund_id, title=payload.title, phone=payload.phone, created_by_id=user_id
        )
        await self.db.commit()
        return EmergencyContactOut.model_validate(contact)

    async def delete(self, fund_id: int, contact_id: int) -> None:
        contact = await self.repo.get(fund_id, contact_id)
        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        await self.repo.delete(contact)
        await self.db.commit()

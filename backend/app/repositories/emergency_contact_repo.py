from sqlalchemy import func, select

from app.models.emergency_contact import EmergencyContact
from app.repositories.base_repo import BaseRepository


class EmergencyContactRepository(BaseRepository):

    async def list(self, fund_id: int) -> list[EmergencyContact]:
        result = await self.db.execute(
            select(EmergencyContact).where(EmergencyContact.fund_id == fund_id).order_by(EmergencyContact.id)
        )
        return list(result.scalars().all())

    async def count(self, fund_id: int) -> int:
        result = await self.db.execute(
            select(func.count(EmergencyContact.id)).where(EmergencyContact.fund_id == fund_id)
        )
        return result.scalar() or 0

    async def get(self, fund_id: int, contact_id: int) -> EmergencyContact | None:
        result = await self.db.execute(
            select(EmergencyContact).where(EmergencyContact.id == contact_id, EmergencyContact.fund_id == fund_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **fields) -> EmergencyContact:
        contact = EmergencyContact(**fields)
        self.db.add(contact)
        await self.db.flush()
        await self.db.refresh(contact)
        return contact

    async def delete(self, contact: EmergencyContact) -> None:
        await self.db.delete(contact)
        await self.db.flush()

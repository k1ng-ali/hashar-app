from datetime import datetime

from sqlalchemy import delete, select, update

from app.models.verification import TrustedDevice, VerificationCode
from app.repositories.base_repo import BaseRepository


class VerificationRepository(BaseRepository):

    # ─── Коды из SMS ───────────────────────────────────────────────────────────

    async def last_code(self, user_id: int, for_update: bool = False) -> VerificationCode | None:
        stmt = (
            select(VerificationCode)
            .where(VerificationCode.user_id == user_id)
            .order_by(VerificationCode.id.desc())
            .limit(1)
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_code(
        self, user_id: int, phone: str, code_hash: str, expires_at: datetime, now: datetime
    ) -> VerificationCode:
        code = VerificationCode(
            user_id=user_id, phone=phone, code_hash=code_hash, expires_at=expires_at, attempts=0, created_at=now
        )
        self.db.add(code)
        await self.db.flush()
        return code

    async def consume_codes(self, user_id: int, now: datetime) -> None:
        """Гасит все живые коды: новый код отменяет старый."""
        await self.db.execute(
            update(VerificationCode)
            .where(VerificationCode.user_id == user_id, VerificationCode.consumed_at.is_(None))
            .values(consumed_at=now)
        )

    # ─── Подтверждённые устройства ─────────────────────────────────────────────

    async def get_device(self, user_id: int, token_hash: str) -> TrustedDevice | None:
        result = await self.db.execute(
            select(TrustedDevice).where(TrustedDevice.user_id == user_id, TrustedDevice.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    def add_device(self, user_id: int, token_hash: str, user_agent: str | None, expires_at: datetime) -> None:
        self.db.add(TrustedDevice(user_id=user_id, token_hash=token_hash, user_agent=user_agent, expires_at=expires_at))

    async def delete_devices(self, user_id: int) -> None:
        """Забыть все устройства — при выходе везде и смене пароля: дальше вход только с подтверждением."""
        await self.db.execute(delete(TrustedDevice).where(TrustedDevice.user_id == user_id))

    async def delete_all(self, user_id: int) -> None:
        """Устройства вместе с User-Agent и коды с номером — при удалении аккаунта."""
        await self.delete_devices(user_id)
        await self.db.execute(delete(VerificationCode).where(VerificationCode.user_id == user_id))

from datetime import datetime

from pydantic import BaseModel


class AuditEventOut(BaseModel):
    id: int
    action: str
    entity: str
    entity_id: int | None = None
    details: dict
    actor_id: int | None = None
    actor_name: str | None = None
    created_at: datetime

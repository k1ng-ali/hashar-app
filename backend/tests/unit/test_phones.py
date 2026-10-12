from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.schemas.auth import RegisterIn
from app.schemas.emergency_contact import EmergencyContactIn
from app.services.emergency_contact_service import MAX_CONTACTS, EmergencyContactService
from tests.unit.helpers import make_db


def test_register_rejects_short_phone():
    with pytest.raises(ValueError):
        RegisterIn(full_name="Али", phone="99921", password="secret1")


def test_register_accepts_formatted_phone_and_email_only():
    assert RegisterIn(full_name="Али", phone="+992 90 123 45 67", password="secret1").phone
    assert RegisterIn(full_name="Али", phone="", email="ali@mail.tj", password="secret1").phone is None


def test_emergency_contact_phone_is_formatted():
    contact = EmergencyContactIn(title="  Медпункт ", phone="992372210303")
    assert contact.title == "Медпункт"
    assert contact.phone == "+992 37 221 03 03"

    with pytest.raises(ValueError):
        EmergencyContactIn(title="Пожарная", phone="101")


async def test_emergency_contacts_are_limited():
    db = make_db()
    service = EmergencyContactService(db=db)
    service.repo.count = AsyncMock(return_value=MAX_CONTACTS)

    with pytest.raises(HTTPException) as exc:
        await service.create(fund_id=1, user_id=1, payload=EmergencyContactIn(title="Медпункт", phone="+992372210303"))

    assert exc.value.status_code == 409
    db.commit.assert_not_called()

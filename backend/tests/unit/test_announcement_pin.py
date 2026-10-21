"""Закрепление и открепление объявлений советом."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.enums import FundRoleEnum
from app.services.announcement_service import AnnouncementService
from tests.unit.helpers import make_ctx, make_db, make_user


def make_announcement(is_pinned: bool):
    return SimpleNamespace(
        id=1, fund_id=1, title="Собрание", content="В субботу", category="meeting", is_pinned=is_pinned,
        author_id=1, author=make_user(), comments=[], transfer=None, transfer_id=None,
        created_at=datetime.now(timezone.utc),
    )  # fmt: skip


def make_service(announcement):
    db = make_db()
    service = AnnouncementService(db=db)
    service.repo.get = AsyncMock(return_value=announcement)
    service.repo.likes_count = AsyncMock(return_value={})
    service.repo.liked_ids = AsyncMock(return_value=set())
    service.member_repo.units_by_users = AsyncMock(return_value={})
    return db, service


async def test_unpin_announcement_writes_audit():
    announcement = make_announcement(is_pinned=True)
    db, service = make_service(announcement)

    result = await service.set_pinned(make_ctx(role=FundRoleEnum.admin), announcement_id=1, is_pinned=False)

    assert result.is_pinned is False and announcement.is_pinned is False
    [event] = [call.args[0] for call in db.add.call_args_list]
    assert event.action == "announcement.unpin" and event.entity_id == 1
    db.commit.assert_awaited_once()


async def test_pin_same_state_is_noop():
    db, service = make_service(make_announcement(is_pinned=True))

    result = await service.set_pinned(make_ctx(role=FundRoleEnum.chairman), announcement_id=1, is_pinned=True)

    assert result.is_pinned is True
    db.add.assert_not_called()
    db.commit.assert_not_called()


async def test_pin_missing_announcement_is_404():
    _, service = make_service(None)
    with pytest.raises(HTTPException) as exc:
        await service.set_pinned(make_ctx(role=FundRoleEnum.chairman), announcement_id=9, is_pinned=True)
    assert exc.value.status_code == 404

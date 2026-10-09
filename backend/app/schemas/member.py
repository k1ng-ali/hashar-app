from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.enums import FundRoleEnum, MemberStatusEnum
from app.schemas.balance import ResidentBalanceOut


class FundContext(BaseModel):
    """Активное членство текущего пользователя в фонде из URL (результат deps.fund)."""

    fund_id: int
    user_id: int
    member_id: int
    role: FundRoleEnum

    @property
    def is_council(self) -> bool:
        return self.role in (FundRoleEnum.admin, FundRoleEnum.chairman)

    @property
    def is_chairman(self) -> bool:
        return self.role == FundRoleEnum.chairman


class JoinIn(BaseModel):
    address_unit: str = Field(min_length=1, max_length=50)
    message: str | None = Field(None, max_length=500)


class MemberOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    phone: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    role: FundRoleEnum
    status: MemberStatusEnum
    address_unit: str | None = None
    message: str | None = None
    joined_at: datetime | None = None
    created_at: datetime


class MemberOutCouncil(MemberOut):
    balance: ResidentBalanceOut | None = None  # только у активных участников


class MemberStatusUpdateIn(BaseModel):
    status: Literal[MemberStatusEnum.active, MemberStatusEnum.blocked]


class MemberRoleUpdateIn(BaseModel):
    role: Literal[FundRoleEnum.resident, FundRoleEnum.admin]


class ChairmanTransferIn(BaseModel):
    member_id: int

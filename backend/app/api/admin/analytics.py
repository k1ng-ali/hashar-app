from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.deps.auth import require_platform_admin
from app.deps.services import get_analytics_service
from app.enums import PlanEnum
from app.schemas.analytics import (
    AuditEventOutAdmin,
    FundHealthListOut,
    FundSort,
    PlatformOverviewOut,
    PlatformPlansOut,
    UserDetailOutAdmin,
    UserListOutAdmin,
)
from app.schemas.user import CurrentUser
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["Admin • Analytics"])


# ─── Аналитика ────────────────────────────────────────────────────────────────


@router.get("/analytics/overview", response_model=PlatformOverviewOut)
async def get_overview(
    months: int = Query(12, ge=1, le=36),
    user: CurrentUser = Depends(require_platform_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.overview(months=months)


@router.get("/analytics/plans", response_model=PlatformPlansOut)
async def get_plans(
    months: int = Query(12, ge=1, le=36),
    user: CurrentUser = Depends(require_platform_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.plans(months=months)


@router.get("/analytics/funds", response_model=FundHealthListOut)
async def list_fund_health(
    q: str | None = Query(None, max_length=100),
    plan: PlanEnum | None = None,
    inactive: bool = False,
    sort: FundSort = "created",
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: CurrentUser = Depends(require_platform_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.funds(query=q, plan=plan, inactive_only=inactive, sort=sort, skip=skip, limit=limit)


# ─── Пользователи ─────────────────────────────────────────────────────────────


@router.get("/users", response_model=UserListOutAdmin)
async def list_users(
    q: str | None = Query(None, max_length=100),
    filter: Literal["all", "unverified", "admins", "deleted"] = "all",
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: CurrentUser = Depends(require_platform_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.users(query=q, filter=filter, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=UserDetailOutAdmin)
async def get_user(
    user_id: int,
    user: CurrentUser = Depends(require_platform_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.user(user_id=user_id)


# ─── Журнал действий ──────────────────────────────────────────────────────────


@router.get("/audit", response_model=list[AuditEventOutAdmin])
async def list_audit(
    fund_id: int | None = None,
    actor_id: int | None = None,
    entity: str | None = Query(None, max_length=30),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: CurrentUser = Depends(require_platform_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.audit(fund_id=fund_id, actor_id=actor_id, entity=entity, skip=skip, limit=limit)

# isort: skip_file
from fastapi import APIRouter

# ─── Auth ─────────────────────────────────────────────────────────────────────
from app.api.auth import router as auth_router

# ─── Platform ─────────────────────────────────────────────────────────────────
from app.api.platform.funds import router as platform_funds_router
from app.api.platform.dashboard import router as platform_dashboard_router
from app.api.platform.contributions import router as platform_contributions_router
from app.api.platform.target_funds import router as platform_target_funds_router
from app.api.platform.expenses import router as platform_expenses_router
from app.api.platform.announcements import router as platform_announcements_router
from app.api.platform.reports import router as platform_reports_router
from app.api.platform.emergency_contacts import router as platform_emergency_router

# ─── Council (совет фонда) ────────────────────────────────────────────────────
from app.api.council.members import router as council_members_router
from app.api.council.contributions import router as council_contributions_router
from app.api.council.expenses import router as council_expenses_router
from app.api.council.target_funds import router as council_target_funds_router
from app.api.council.settings import router as council_settings_router
from app.api.council.transfers import router as council_transfers_router
from app.api.council.plan import router as council_plan_router
from app.api.council.emergency_contacts import router as council_emergency_router

# ─── Admin (админ платформы) ──────────────────────────────────────────────────
from app.api.admin.plans import router as admin_plans_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)

api_router.include_router(platform_funds_router)
api_router.include_router(platform_dashboard_router)
api_router.include_router(platform_contributions_router)
api_router.include_router(platform_target_funds_router)
api_router.include_router(platform_expenses_router)
api_router.include_router(platform_announcements_router)
api_router.include_router(platform_reports_router)
api_router.include_router(platform_emergency_router)

api_router.include_router(council_members_router, prefix="/council")
api_router.include_router(council_contributions_router, prefix="/council")
api_router.include_router(council_expenses_router, prefix="/council")
api_router.include_router(council_target_funds_router, prefix="/council")
api_router.include_router(council_settings_router, prefix="/council")
api_router.include_router(council_transfers_router, prefix="/council")
api_router.include_router(council_plan_router, prefix="/council")
api_router.include_router(council_emergency_router, prefix="/council")

api_router.include_router(admin_plans_router, prefix="/admin")

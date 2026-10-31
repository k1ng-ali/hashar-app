from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.account_service import AccountService
from app.services.analytics_service import AnalyticsService
from app.services.announcement_service import AnnouncementService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.contribution_service import ContributionService
from app.services.dashboard_service import DashboardService
from app.services.emergency_contact_service import EmergencyContactService
from app.services.expense_service import ExpenseService
from app.services.fund_service import FundService
from app.services.member_service import MemberService
from app.services.notice_service import NoticeService
from app.services.plan_service import PlanService
from app.services.pricing_service import PricingService
from app.services.report_service import ReportService
from app.services.target_fund_service import TargetFundService


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db=db)


async def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(db=db)


async def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db=db)


async def get_fund_service(db: AsyncSession = Depends(get_db)) -> FundService:
    return FundService(db=db)


async def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(db=db)


async def get_account_service(db: AsyncSession = Depends(get_db)) -> AccountService:
    return AccountService(db=db)


async def get_member_service(db: AsyncSession = Depends(get_db)) -> MemberService:
    return MemberService(db=db)


async def get_notice_service(db: AsyncSession = Depends(get_db)) -> NoticeService:
    return NoticeService(db=db)


async def get_plan_service(db: AsyncSession = Depends(get_db)) -> PlanService:
    return PlanService(db=db)


async def get_pricing_service(db: AsyncSession = Depends(get_db)) -> PricingService:
    return PricingService(db=db)


async def get_contribution_service(db: AsyncSession = Depends(get_db)) -> ContributionService:
    return ContributionService(db=db)


async def get_expense_service(db: AsyncSession = Depends(get_db)) -> ExpenseService:
    return ExpenseService(db=db)


async def get_target_fund_service(db: AsyncSession = Depends(get_db)) -> TargetFundService:
    return TargetFundService(db=db)


async def get_announcement_service(db: AsyncSession = Depends(get_db)) -> AnnouncementService:
    return AnnouncementService(db=db)


async def get_report_service(db: AsyncSession = Depends(get_db)) -> ReportService:
    return ReportService(db=db)


async def get_emergency_contact_service(db: AsyncSession = Depends(get_db)) -> EmergencyContactService:
    return EmergencyContactService(db=db)

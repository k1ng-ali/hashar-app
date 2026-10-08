from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth,
    users,
    contributions,
    expenses,
    target_funds,
    announcements,
    settings,
    reports,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Авторизация и профиль"])
api_router.include_router(users.router, prefix="/users", tags=["Жильцы и совет дома"])
api_router.include_router(contributions.router, prefix="/contributions", tags=["Взносы и чеки"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["Расходы фонда"])
api_router.include_router(target_funds.router, prefix="/target-funds", tags=["Целевые сборы"])
api_router.include_router(announcements.router, prefix="/announcements", tags=["Доска объявлений"])
api_router.include_router(settings.router, prefix="/settings", tags=["Настройки и реквизиты"])
api_router.include_router(reports.router, prefix="/reports", tags=["Отчеты и выгрузка"])

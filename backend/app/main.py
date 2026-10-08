from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is initialized on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
API системы прозрачного управления локальным общественным фондом (ТСЖ / ЖК).

### Функционал:
- 🏢 **Жильцы и совет дома**: ролевой доступ (SUPERADMIN, ADMIN, RESIDENT).
- 💳 **Взносы и верификация чеков**: отправка чеков жильцами, модерация советом дома.
- 📉 **Расходы фонда**: детальная отчетность, чеки и акты выполненных работ.
- 🎯 **Целевые сборы**: краудфандинг на благоустройство, шлагбаумы, видеонаблюдение.
- 📢 **Доска объявлений**: оповещения совета дома, закрепленные сообщения, комментарии и лайки.
- 📊 **Финансовые отчеты**: помесячная ведомость, контроль задолженностей и экспорт в CSV.
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Служебные"])
def health_check():
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.VERSION}


@app.get("/", tags=["Служебные"])
def root():
    return {
        "message": "API Фонда дома работает",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "redoc_url": f"{settings.API_V1_STR}/redoc",
    }

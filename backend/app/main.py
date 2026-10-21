import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router import api_router
from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import BodySizeLimitMiddleware
from app.jobs import plan_expiry_loop

DEV_MODE = settings.DEV_MODE


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Фоновая проверка окончания тарифов (уведомления совету)
    task = asyncio.create_task(plan_expiry_loop()) if settings.NOTICE_CHECK_INTERVAL > 0 else None
    yield
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title="Hashar API",
    version="0.3.0",
    docs_url="/docs" if DEV_MODE else None,
    redoc_url="/redoc" if DEV_MODE else None,
    openapi_url="/openapi.json" if DEV_MODE else None,
    lifespan=lifespan,
)

# Чеки приходят data URL внутри JSON — режем слишком большие запросы до разбора тела
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.MAX_BODY_BYTES)

# CORS (чтобы фронт на Vue мог ходить к API с cookie). В проде — домен из CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Имя CSV-файла фронтенд берёт из Content-Disposition
    expose_headers=["Content-Disposition"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    res = await db.execute(text("SELECT 1"))
    return {"db": res.scalar()}

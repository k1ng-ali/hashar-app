from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router import api_router
from app.core.config import settings
from app.core.database import get_db

DEV_MODE = settings.DEV_MODE

app = FastAPI(
    title="Fund System API",
    version="0.2.0",
    docs_url="/docs" if DEV_MODE else None,
    redoc_url="/redoc" if DEV_MODE else None,
    openapi_url="/openapi.json" if DEV_MODE else None,
)

# CORS (чтобы фронт на Vue мог ходить к API с cookie)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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

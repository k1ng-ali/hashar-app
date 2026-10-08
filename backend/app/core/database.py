import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

# In local demo/testing without live PostgreSQL running, support SQLite fallback if desired
database_url = os.environ.get("DATABASE_URL") or settings.SQLALCHEMY_DATABASE_URI or "sqlite:///./fund_app.db"

# Connect args needed for SQLite only
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(
    database_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True if not database_url.startswith("sqlite") else False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI Dependency yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

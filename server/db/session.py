# ================================================================
#  db/session.py — Async SQLAlchemy engine + session factory
#  Usage: async with get_session() as session: ...
# ================================================================
from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import DeclarativeBase

from config import settings

# ── Engine ───────────────────────────────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=False,       # set True to log all SQL — useful during dev
    pool_size=10,
    max_overflow=20,
)

# ── Session factory ──────────────────────────────────────────────
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── Base class for all ORM models ────────────────────────────────
class Base(DeclarativeBase):
    pass

# ── Dependency — use in FastAPI route functions ──────────────────
@asynccontextmanager
async def get_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

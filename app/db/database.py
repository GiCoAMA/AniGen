from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

Base = declarative_base()


def _to_async_database_url(database_url: str) -> str:
    """
    Convert a generic SQLAlchemy database URL into an async-capable one.

    - sqlite:///...        -> sqlite+aiosqlite:///...
    - postgresql://...     -> postgresql+asyncpg://...
    """

    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://")
    return database_url


ASYNC_DATABASE_URL = _to_async_database_url(settings.database_url)

# Async SQLAlchemy engine.
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    future=True,
)

# AsyncSession factory.
SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async SQLAlchemy session."""

    async with SessionLocal() as session:
        yield session


"""Database session management for asynchronous SQLModel operations."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models import *  # noqa: F403

async_engine = create_async_engine(
    url=settings.database_url,
    echo=True,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for the duration of a request."""
    session = async_sessionmaker(bind=async_engine, expire_on_commit=False)
    async with session() as s:
        try:
            yield s  # type: ignore [misc]
            await s.commit()
        finally:
            await s.close()


# Optional: create tables for quick local dev (use Alembic in real flows)
async def init_db() -> None:
    """Create database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

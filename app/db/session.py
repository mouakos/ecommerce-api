"""Database session management for asynchronous SQLModel operations."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings
from app.models import *  # noqa: F403

async_engine = create_async_engine(settings.database_url, echo=True)

AsyncSessionLocal = async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for the duration of a request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        finally:
            await session.close()


# Optional: create tables for quick local dev (use Alembic in real flows)
async def init_db() -> None:
    """Create database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

"""Database session management for asynchronous SQLModel operations."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models import *  # noqa: F403

async_engine = AsyncEngine(
    create_engine(
        url=settings.database_url,
        echo=True,
    )
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for the duration of a request."""
    session = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore [call-overload]
    async with session() as s:
        try:
            yield s
            await s.commit()
        finally:
            await s.close()


# Optional: create tables for quick local dev (use Alembic in real flows)
async def init_db() -> None:
    """Create database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

"""Common fixtures for testing."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, text

from app.db.session import get_session
from app.main import app

# Use file-based SQLite to avoid multiple connections losing tables in memory
TEST_DB_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Session-wide event loop for pytest-asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_engine():
    """Create engine & schema once for the test session."""
    engine = create_async_engine(TEST_DB_URL, echo=False, future=True)

    # Create the database schema
    async with engine.begin() as conn:
        # Enable FK constraints in SQLite
        await conn.execute(text("PRAGMA foreign_keys=ON"))

        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Drop the database schema
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Fresh session for each test."""
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture(autouse=True)
def override_get_session(db_session: AsyncSession):
    """Override FastAPI's DB dependency for tests."""

    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

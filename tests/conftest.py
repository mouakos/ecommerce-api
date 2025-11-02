"""Common fixtures for testing."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, text

from app.core.security import get_password_hash
from app.db.session import get_session
from app.main import app
from app.models.user import User
from tests.factories import BaseFactory

# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Session-wide event loop for pytest-asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
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


def bind_factory_session_recursively(factory_class, db_session: AsyncSession):
    """Bind the SQLAlchemy session to the factory and its base classes."""
    factory_class._meta.sqlalchemy_session = db_session
    for sub in factory_class.__subclasses__():
        bind_factory_session_recursively(sub, db_session)


@pytest.fixture(autouse=True)
def override_get_session(db_session: AsyncSession):
    """Override FastAPI's DB dependency for tests."""

    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def set_sqlalchemy_session(db_session: AsyncSession):
    """Set the SQLAlchemy session for the factories."""
    bind_factory_session_recursively(BaseFactory, db_session)
    yield
    bind_factory_session_recursively(BaseFactory, None)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated HTTP client for tests."""
    user = User(role="user", email="user@example.com", hashed_password=get_password_hash("user"))
    db_session.add(user)
    await db_session.flush()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/auth/login",
            data={"username": user.email, "password": "user"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        ac.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
        yield ac


@pytest.fixture
async def auth_admin_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated admin HTTP client for tests."""
    admin_user = User(
        role="admin", email="admin@example.com", hashed_password=get_password_hash("admin")
    )
    db_session.add(admin_user)
    await db_session.flush()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/auth/login",
            data={"username": admin_user.email, "password": "admin"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        ac.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
        yield ac

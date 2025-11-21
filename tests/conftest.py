"""Common fixtures for testing.

Respects optional TEST_DATABASE_URL without touching production DATABASE_URL.
If TEST_DATABASE_URL is unset, falls back to ephemeral in-memory SQLite.
This avoids accidentally running tests against a production database while
allowing CI to export DATABASE_URL separately.
"""

from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine, text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import get_password_hash
from app.db.session import get_session
from app.main import app
from app.models.address import Address
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from tests.factories import BaseFactory


@pytest.fixture
async def async_engine() -> AsyncGenerator[Engine, None]:
    """Create engine & schema once for the test session."""
    async_engine = AsyncEngine(
        create_engine(
            url=settings.test_database_url,
            echo=True,
        )
    )

    # Create the database schema
    async with async_engine.begin() as conn:
        if settings.test_database_url.startswith("sqlite"):
            # Enable FK constraints in SQLite
            await conn.execute(text("PRAGMA foreign_keys=ON"))

        await conn.run_sync(SQLModel.metadata.create_all)

    yield async_engine

    # Drop the database schema
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await async_engine.dispose()


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Fresh session for each test."""
    async_session = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
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
def category_factory(db_session: AsyncSession):
    async def _create(name: str):
        category = Category(name=name)
        db_session.add(category)
        await db_session.flush()
        await db_session.refresh(category)
        return category

    return _create


@pytest.fixture
def product_factory(db_session: AsyncSession, category_factory):
    async def _create(
        name: str,
        *,
        category: Category | None = None,
        category_name: str | None = None,
        description: str = "desc",
        price: float = 10.0,
        stock: int = 5,
    ):
        if category is None:
            if category_name is None:
                category_name = f"cat-{name}"
            category = await category_factory(category_name)
        product = Product(
            name=name, description=description, price=price, stock=stock, category_id=category.id
        )
        db_session.add(product)
        await db_session.flush()
        await db_session.refresh(product)
        return product

    return _create


@pytest.fixture
def address_factory(db_session: AsyncSession):
    async def _create(
        user_id: UUID,
        *,
        line1: str = "123 Main St",
        line2: str | None = None,
        city: str = "City",
        state: str = "ST",
        postal_code: str = "00000",
        country: str = "us",
        first_name: str | None = None,
        last_name: str | None = None,
        company: str | None = None,
        phone_number: str | None = None,
    ):
        addr = Address(
            user_id=user_id,
            line1=line1,
            line2=line2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            first_name=first_name,
            last_name=last_name,
            company=company,
            phone_number=phone_number,
        )
        db_session.add(addr)
        await db_session.flush()
        await db_session.refresh(addr)
        return addr

    return _create


@pytest.fixture
def verified_user_factory(user_factory):
    async def _create(email: str, password: str = "secret123"):
        return await user_factory(email=email, password=password, is_verified=True)

    return _create


@pytest.fixture
def user_factory(db_session: AsyncSession):
    async def _create(
        email: str,
        password: str = "Pass123",
        role: str = "user",
        is_verified: bool = True,
    ):
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            is_verified=is_verified,
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)
        return user

    return _create


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated HTTP client for tests using JSON login payload."""
    user = User(
        role="user",
        email="user@example.com",
        hashed_password=get_password_hash("user123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "user123"},
        )
        ac.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
        yield ac


@pytest.fixture
async def auth_client1(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Second authenticated HTTP client (JSON login)."""
    user = User(
        role="user",
        email="user1@example.com",
        hashed_password=get_password_hash("user12"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "user12"},
        )
        ac.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
        yield ac


@pytest.fixture
async def auth_admin_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated admin HTTP client for tests (JSON login)."""
    admin_user = User(
        role=UserRole.ADMIN,
        email="admin@example.com",
        hashed_password=get_password_hash("admin1"),
        is_verified=True,
    )
    db_session.add(admin_user)
    await db_session.flush()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/auth/login",
            json={"email": admin_user.email, "password": "admin1"},
        )
        ac.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
        yield ac

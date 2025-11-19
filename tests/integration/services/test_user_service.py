"""Unit tests for UserService."""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import UserNotFoundError
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_update_profile_success(db_session: AsyncSession):
    user = await AuthService.create_user(
        db_session, UserCreate(email="profile@example.com", password="secret123")
    )
    updated = await UserService.update_profile(
        db_session,
        user.id,
        UserUpdate(first_name="Alice", last_name="Tester", phone_number="+123456789"),
    )
    assert updated.first_name == "Alice"
    assert updated.last_name == "Tester"
    assert updated.phone_number == "+123456789"


@pytest.mark.asyncio
async def test_update_profile_user_not_found(db_session: AsyncSession):
    import uuid

    with pytest.raises(UserNotFoundError):
        await UserService.update_profile(db_session, uuid.uuid4(), UserUpdate(first_name="Ghost"))


@pytest.mark.asyncio
async def test_list_and_search_users(db_session: AsyncSession):
    await AuthService.create_user(
        db_session, UserCreate(email="alpha@example.com", password="secret123")
    )
    await AuthService.create_user(
        db_session, UserCreate(email="beta@example.com", password="secret123")
    )
    items, total = await UserService.list(db_session, limit=10, offset=0)
    assert total >= 2
    # search by partial
    search_items, search_total = await UserService.list(
        db_session, limit=10, offset=0, search="alpha"
    )
    assert search_total >= 1
    assert any("alpha" in u.email for u in search_items)


@pytest.mark.asyncio
async def test_deactivate_and_activate(db_session: AsyncSession):
    user = await AuthService.create_user(
        db_session, UserCreate(email="toggle@example.com", password="secret123")
    )
    await UserService.deactivate(db_session, user.id)
    fetched = await UserService.get(db_session, user.id)
    assert fetched.is_active is False
    await UserService.activate(db_session, user.id)
    fetched2 = await UserService.get(db_session, user.id)
    assert fetched2.is_active is True


@pytest.mark.asyncio
async def test_set_role(db_session: AsyncSession):
    user = await AuthService.create_user(
        db_session, UserCreate(email="role@example.com", password="secret123")
    )
    await UserService.set_role(db_session, user.id, "admin")
    changed = await UserService.get(db_session, user.id)
    assert changed.role == "admin"

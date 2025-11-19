"""Unit tests for AuthService logic.

These focus on business rules (existence checks, password hashing, verification flag changes)
without going through HTTP routes. Uses the shared async SQLModel test session fixtures from
`tests/conftest.py` (db_session override of get_session) and exercises error paths.
"""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import (
    InvalidCredentialsError,
    PasswordMismatchError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import verify_password
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_create_user_success(db_session: AsyncSession):
    data = UserCreate(email="alice@example.com", password="Secret123")
    user = await AuthService.create_user(db_session, data)
    assert user.id is not None
    assert user.email == data.email
    assert verify_password("Secret123", user.hashed_password)


@pytest.mark.asyncio
async def test_create_user_duplicate_email(db_session: AsyncSession):
    data = UserCreate(email="dup@example.com", password="pass1234")
    first = await AuthService.create_user(db_session, data)
    assert first.email == data.email
    with pytest.raises(UserAlreadyExistsError):
        await AuthService.create_user(db_session, data)


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session: AsyncSession):
    data = UserCreate(email="login@example.com", password="LoginPass9")
    user = await AuthService.create_user(db_session, data)
    authed = await AuthService.authenticate_user(db_session, user.email, data.password)
    assert authed.id == user.id


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session: AsyncSession):
    data = UserCreate(email="wrongpw@example.com", password="RightPass8")
    await AuthService.create_user(db_session, data)
    with pytest.raises(InvalidCredentialsError):
        await AuthService.authenticate_user(db_session, data.email, "WrongPass8")


@pytest.mark.asyncio
async def test_authenticate_user_unknown_email(db_session: AsyncSession):
    with pytest.raises(InvalidCredentialsError):
        await AuthService.authenticate_user(db_session, "missing@example.com", "whatever1")


@pytest.mark.asyncio
async def test_verify_user_email_sets_flag(db_session: AsyncSession):
    data = UserCreate(email="verifyme@example.com", password="Ver1fyPwd")
    user = await AuthService.create_user(db_session, data)
    assert user.is_verified is False
    await AuthService.verify_user_email(db_session, user.email)
    # refresh state
    refreshed = await AuthService.get_user_by_email(db_session, user.email)
    assert refreshed is not None
    assert refreshed.is_verified is True


@pytest.mark.asyncio
async def test_verify_user_email_missing_user(db_session: AsyncSession):
    with pytest.raises(UserNotFoundError):
        await AuthService.verify_user_email(db_session, "nouser@example.com")


@pytest.mark.asyncio
async def test_change_user_password_success(db_session: AsyncSession):
    data = UserCreate(email="changepw@example.com", password="OldPass77")
    user = await AuthService.create_user(db_session, data)
    await AuthService.change_user_password(
        db_session,
        user.email,
        "NewPass88",
        "NewPass88",
    )
    updated = await AuthService.get_user_by_email(db_session, user.email)
    assert updated is not None
    assert verify_password("NewPass88", updated.hashed_password)
    assert not verify_password("OldPass77", updated.hashed_password)


@pytest.mark.asyncio
async def test_change_user_password_mismatch(db_session: AsyncSession):
    data = UserCreate(email="mismatch@example.com", password="OrigPass66")
    await AuthService.create_user(db_session, data)
    with pytest.raises(PasswordMismatchError):
        await AuthService.change_user_password(
            db_session,
            data.email,
            "NewPass!!",
            "Different!!",
        )


@pytest.mark.asyncio
async def test_change_user_password_user_not_found(db_session: AsyncSession):
    with pytest.raises(UserNotFoundError):
        await AuthService.change_user_password(
            db_session,
            "absent@example.com",
            "SomePass11",
            "SomePass11",
        )

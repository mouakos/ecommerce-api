"""Unit tests for AddressService (defaults removed).

Cover now:
 - Basic create
 - Update fields
 - Ownership enforcement (wrong user id raises AddressNotFoundError)
 - Delete lifecycle
 - Pagination basics
"""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import AddressNotFoundError
from app.schemas.address import AddressCreate, AddressUpdate
from app.services.address_service import AddressService


def _payload(label: str) -> AddressCreate:
    return AddressCreate(
        line1=f"{label} Street",
        city="City",
        state="ST",
        postal_code="12345",
        country="us",
    )


@pytest.mark.asyncio
async def test_create_address(db_session: AsyncSession, user_factory):
    user = await user_factory("addr-first@example.com")
    addr = await AddressService.create(db_session, user.id, _payload("Home"))
    assert addr.line1.startswith("Home")


@pytest.mark.asyncio
async def test_update_address(db_session: AsyncSession, user_factory):
    user = await user_factory("addr-update@example.com")
    addr = await AddressService.create(db_session, user.id, _payload("Primary"))
    updated = await AddressService.update(
        db_session, addr.id, user.id, AddressUpdate(line1="New Primary St")
    )
    assert updated.line1 == "New Primary St"


@pytest.mark.asyncio
async def test_list_addresses(db_session: AsyncSession, user_factory):
    user = await user_factory("addr-list@example.com")
    for i in range(2):
        await AddressService.create(db_session, user.id, _payload(f"L{i}"))
    items, total = await AddressService.list(db_session, user.id)
    assert total == 2
    assert all(a.line1.endswith("Street") for a in items)


@pytest.mark.asyncio
# (Removed shipping default update test)


@pytest.mark.asyncio
async def test_get_wrong_user_raises_not_found(db_session: AsyncSession, user_factory):
    owner = await user_factory("addr-owner@example.com")
    intruder = await user_factory("addr-intruder@example.com")
    addr = await AddressService.create(db_session, owner.id, _payload("Secret"))
    with pytest.raises(AddressNotFoundError):
        await AddressService.get(db_session, addr.id, intruder.id)


@pytest.mark.asyncio
async def test_delete_address_and_not_found(db_session: AsyncSession, user_factory):
    user = await user_factory("addr-del@example.com")
    addr = await AddressService.create(db_session, user.id, _payload("Del"))
    await AddressService.delete(db_session, addr.id, user.id)
    with pytest.raises(AddressNotFoundError):
        await AddressService.get(db_session, addr.id, user.id)
    # deleting again raises
    with pytest.raises(AddressNotFoundError):
        await AddressService.delete(db_session, addr.id, user.id)


@pytest.mark.asyncio
async def test_list_pagination(db_session: AsyncSession, user_factory):
    user = await user_factory("addr-page@example.com")
    for i in range(3):
        await AddressService.create(db_session, user.id, _payload(f"P{i}"))
    items1, total = await AddressService.list(db_session, user.id, limit=2, offset=0)
    items2, _ = await AddressService.list(db_session, user.id, limit=2, offset=2)
    assert total == 3
    assert len(items1) == 2
    assert len(items2) == 1

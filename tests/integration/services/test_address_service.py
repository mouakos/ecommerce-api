"""Unit tests for AddressService.

Cover:
 - First address auto defaults (shipping & billing)
 - Explicit shipping default switch on second create
 - Setting billing default via service method
 - Updating an address to become default shipping
 - Ownership enforcement (wrong user id raises AddressNotFoundError)
 - Delete lifecycle (delete then not found on get & second delete raises)
 - Pagination basics (limit/offset & total count)
"""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import AddressNotFoundError
from app.schemas.address import AddressCreate, AddressUpdate
from app.services.address_service import AddressService


def _payload(label: str) -> AddressCreate:
    return AddressCreate(
        label=label,
        line1=f"{label} line1",
        city="City",
        postal_code="12345",
        country="us",
    )


@pytest.mark.asyncio
async def test_create_first_address_sets_defaults(db_session: AsyncSession, user_factory):
    user = await user_factory("addr-first@example.com")
    addr = await AddressService.create(db_session, user.id, _payload("Home"))
    assert addr.is_default_shipping is True
    assert addr.is_default_billing is True


@pytest.mark.asyncio
async def test_create_second_address_explicit_shipping_default_switches(
    db_session: AsyncSession, user_factory
):
    user = await user_factory("addr-second@example.com")
    first = await AddressService.create(db_session, user.id, _payload("Primary"))
    second_payload = _payload("Secondary")
    second_payload.set_default_shipping = True
    second = await AddressService.create(db_session, user.id, second_payload)
    # Reload via list
    items, total = await AddressService.list(db_session, user.id)
    assert total == 2
    shipping_defaults = [a.id for a in items if a.is_default_shipping]
    assert shipping_defaults == [second.id]
    assert first.is_default_billing is True  # billing default remains on first
    assert second.is_default_billing is False


@pytest.mark.asyncio
async def test_set_default_billing_switches(db_session: AsyncSession, user_factory):
    user = await user_factory("addr-billing@example.com")
    first = await AddressService.create(db_session, user.id, _payload("A1"))
    second = await AddressService.create(db_session, user.id, _payload("A2"))
    # make second billing default
    updated = await AddressService.set_default_billing(db_session, second.id, user.id)
    assert updated.id == second.id
    items, _ = await AddressService.list(db_session, user.id)
    billing_defaults = [a.id for a in items if a.is_default_billing]
    assert billing_defaults == [second.id]
    # ensure first lost billing default
    assert first.id not in billing_defaults


@pytest.mark.asyncio
async def test_update_address_set_default_shipping(db_session: AsyncSession, user_factory):
    user = await user_factory("addr-update@example.com")
    first = await AddressService.create(db_session, user.id, _payload("U1"))
    second = await AddressService.create(db_session, user.id, _payload("U2"))
    # Make second shipping default via update
    updated = await AddressService.update(
        db_session, second.id, user.id, AddressUpdate(set_default_shipping=True)
    )
    assert updated.is_default_shipping is True
    items, _ = await AddressService.list(db_session, user.id)
    shipping_defaults = [a.id for a in items if a.is_default_shipping]
    assert shipping_defaults == [second.id]
    assert first.id not in shipping_defaults


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

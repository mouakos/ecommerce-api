"""Service layer for Address operations."""

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.errors import AddressNotFoundError
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate


class AddressService:
    """CRUD and default management for addresses."""

    @staticmethod
    async def list(
        db: AsyncSession, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> tuple[list[Address], int]:
        """Return a paginated list of addresses for a user."""
        stmt = select(Address).where(Address.user_id == user_id).offset(offset).limit(limit)
        res = await db.execute(stmt)
        items: list[Address] = list(res.scalars().all())
        count_stmt = select(Address).where(Address.user_id == user_id)
        count_res = await db.execute(count_stmt)
        total = len(count_res.scalars().all())
        return items, total

    @staticmethod
    async def get(db: AsyncSession, address_id: UUID, user_id: UUID | None = None) -> Address:
        """Fetch an address by id enforcing optional ownership."""
        stmt = select(Address).where(Address.id == address_id)
        if user_id is not None:
            stmt = stmt.where(Address.user_id == user_id)
        res = await db.execute(stmt)
        address = res.scalar_one_or_none()
        if not address:
            raise AddressNotFoundError()
        return address

    @staticmethod
    async def create(db: AsyncSession, user_id: UUID, payload: AddressCreate) -> Address:
        """Create a new address; optionally set defaults if first or flags provided."""
        addr = Address(
            user_id=user_id,
            **payload.model_dump(exclude={"set_default_shipping", "set_default_billing"}),
        )
        db.add(addr)
        await db.flush()
        # Fetch existing addresses to determine defaults
        existing_stmt = select(Address).where(Address.user_id == user_id)
        existing_res = await db.execute(existing_stmt)
        existing_addresses = list(existing_res.scalars().all())
        has_shipping_default = any(
            a.is_default_shipping for a in existing_addresses if a.id != addr.id
        )
        has_billing_default = any(
            a.is_default_billing for a in existing_addresses if a.id != addr.id
        )
        # Set shipping default if explicitly requested or if none exists yet
        if payload.set_default_shipping or not has_shipping_default:
            await AddressService._maybe_set_default(db, user_id, addr, shipping=True, force=True)
        # Set billing default if explicitly requested or if none exists yet
        if payload.set_default_billing or not has_billing_default:
            await AddressService._maybe_set_default(db, user_id, addr, billing=True, force=True)
        return addr

    @staticmethod
    async def update(
        db: AsyncSession, address_id: UUID, user_id: UUID, payload: AddressUpdate
    ) -> Address:
        """Update an existing address and handle default flags."""
        addr = await AddressService.get(db, address_id, user_id)
        data = payload.model_dump(exclude_unset=True)
        flags = {}
        for field, value in list(data.items()):
            if field in {"set_default_shipping", "set_default_billing"}:
                flags[field] = value
                continue
            setattr(addr, field, value)
        await db.flush()
        if flags.get("set_default_shipping") is True:
            await AddressService._maybe_set_default(db, user_id, addr, shipping=True, force=True)
        if flags.get("set_default_billing") is True:
            await AddressService._maybe_set_default(db, user_id, addr, billing=True, force=True)
        return addr

    @staticmethod
    async def delete(db: AsyncSession, address_id: UUID, user_id: UUID) -> None:
        """Delete an address owned by the user."""
        addr = await AddressService.get(db, address_id, user_id)
        await db.delete(addr)
        await db.flush()

    @staticmethod
    async def set_default_shipping(db: AsyncSession, address_id: UUID, user_id: UUID) -> Address:
        """Mark an address as default shipping, clearing previous default."""
        addr = await AddressService.get(db, address_id, user_id)
        await AddressService._maybe_set_default(db, user_id, addr, shipping=True, force=True)
        return addr

    @staticmethod
    async def set_default_billing(db: AsyncSession, address_id: UUID, user_id: UUID) -> Address:
        """Mark an address as default billing, clearing previous default."""
        addr = await AddressService.get(db, address_id, user_id)
        await AddressService._maybe_set_default(db, user_id, addr, billing=True, force=True)
        return addr

    @staticmethod
    async def _maybe_set_default(
        db: AsyncSession,
        user_id: UUID,
        target: Address,
        shipping: bool = False,
        billing: bool = False,
        force: bool = False,
    ) -> None:
        if not (shipping or billing):
            return
        # Query existing defaults
        stmt = select(Address).where(Address.user_id == user_id)
        res = await db.execute(stmt)
        addresses: Iterable[Address] = res.scalars().all()
        has_any = False
        for addr in addresses:
            has_any = True
            if shipping and addr.is_default_shipping and (force or addr.id != target.id):
                addr.is_default_shipping = False
            if billing and addr.is_default_billing and (force or addr.id != target.id):
                addr.is_default_billing = False
        if (
            shipping
            and (force or not target.is_default_shipping)
            and (force or not has_any or not any(a.is_default_shipping for a in addresses))
        ):
            target.is_default_shipping = True
        if (
            billing
            and (force or not target.is_default_billing)
            and (force or not has_any or not any(a.is_default_billing for a in addresses))
        ):
            target.is_default_billing = True
        await db.flush()

"""Service layer for Address operations."""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import AddressNotFoundError
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate


class AddressService:
    """CRUD operations for addresses (default flags removed)."""

    @staticmethod
    async def list(
        db: AsyncSession, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> tuple[list[Address], int]:
        """List addresses for a user with pagination.

        Args:
            db (AsyncSession): Database session.
            user_id (UUID): User identifier to filter addresses.
            offset (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 50.

        Returns:
            tuple[list[Address], int]: A tuple containing a list of Address objects and the total count of addresses.
        """
        stmt = select(Address).where(Address.user_id == user_id).offset(offset).limit(limit)
        res = await db.exec(stmt)
        items: list[Address] = list(res.all())
        count_stmt = select(Address).where(Address.user_id == user_id)
        count_res = await db.exec(count_stmt)
        total = len(count_res.all())
        return items, total

    @staticmethod
    async def get(db: AsyncSession, address_id: UUID, user_id: UUID | None = None) -> Address:
        """Fetch an address by id enforcing optional ownership.

        Args:
            db (AsyncSession): Database session.
            address_id (UUID): Address identifier.
            user_id (UUID | None, optional): User identifier to enforce ownership. Defaults to None.

        Raises:
            AddressNotFoundError: If the address does not exist or does not belong to the user.

        Returns:
            Address: The requested address.
        """
        stmt = select(Address).where(Address.id == address_id)
        if user_id is not None:
            stmt = stmt.where(Address.user_id == user_id)
        res = await db.exec(stmt)
        address = res.first()
        if not address:
            raise AddressNotFoundError()
        return address

    @staticmethod
    async def create(db: AsyncSession, user_id: UUID, payload: AddressCreate) -> Address:
        """Create a new address.

        Args:
            db (AsyncSession): Database session.
            user_id (UUID): User identifier.
            payload (AddressCreate): Address creation payload.

        Returns:
            Address: The newly created address.
        """
        addr = Address(user_id=user_id, **payload.model_dump())
        db.add(addr)
        await db.flush()
        return addr

    @staticmethod
    async def update(
        db: AsyncSession, address_id: UUID, user_id: UUID, payload: AddressUpdate
    ) -> Address:
        """Update an existing address.

        Args:
            db (AsyncSession): Database session.
            address_id (UUID): Address identifier.
            user_id (UUID): User identifier.
            payload (AddressUpdate): Address update payload.

        Returns:
            Address: The updated address.

        Raises:
            AddressNotFoundError: If the address does not exist or does not belong to the user
        """
        addr = await AddressService.get(db, address_id, user_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(addr, field, value)
        await db.flush()
        return addr

    @staticmethod
    async def delete(db: AsyncSession, address_id: UUID, user_id: UUID) -> None:
        """Delete an address owned by the user.

        Args:
            db (AsyncSession): Database session.
            address_id (UUID): Address identifier.
            user_id (UUID): User identifier.

        Raises:
            AddressNotFoundError: If the address does not exist or does not belong to the user
        """
        addr = await AddressService.get(db, address_id, user_id)
        await db.delete(addr)
        await db.flush()

"""API routes for managing user addresses."""

# mypy: disable-error-code=return-value

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker, get_current_user
from app.core.enums import UserRole
from app.db.session import get_session
from app.models.user import User
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate
from app.schemas.base import Page
from app.services.address_service import AddressService

router = APIRouter(prefix="/api/v1/addresses", tags=["Addresses"])
admin_role = Depends(RoleChecker([UserRole.ADMIN]))


@router.get("/", response_model=Page[AddressRead])
async def list_my_addresses(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Page[AddressRead]:
    """List addresses for current user."""
    items, total = await AddressService.list(db, current_user.id, offset=offset, limit=limit)
    return Page[AddressRead](items=items, total=total, limit=limit, offset=offset)


@router.post("/", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
async def create_address(
    payload: AddressCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AddressRead:
    """Create a new address for current user."""
    return await AddressService.create(db, current_user.id, payload)


@router.get("/{address_id}", response_model=AddressRead)
async def get_address(
    address_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AddressRead:
    """Get an address owned by current user."""
    return await AddressService.get(db, address_id, current_user.id)


@router.patch("/{address_id}", response_model=AddressRead)
async def update_address(
    address_id: UUID,
    payload: AddressUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AddressRead:
    """Update an address owned by current user."""
    return await AddressService.update(db, address_id, current_user.id, payload)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete an address owned by current user (204)."""
    await AddressService.delete(db, address_id, current_user.id)


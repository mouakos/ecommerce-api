"""API routes for user management (admin + self profile)."""
# mypy: disable-error-code=return-value

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import RoleChecker, get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.address import AddressRead
from app.schemas.base import Page
from app.schemas.user import UserRead, UserRoleUpdate, UserUpdate
from app.services.address_service import AddressService
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["Users"])
role_checker = Depends(RoleChecker(["admin"]))


@router.get("/", response_model=Page[UserRead], dependencies=[role_checker])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, min_length=1),
) -> Page[UserRead]:
    """List users (admin only) with optional email search and pagination."""
    users, total = await UserService.list(db, limit=limit, offset=offset, search=search)
    return Page[UserRead](items=users, total=total, limit=limit, offset=offset)


@router.get("/me", response_model=UserRead)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    """Get the current authenticated user."""
    return current_user


@router.get("/{user_id}", response_model=UserRead, dependencies=[role_checker])
async def get_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> UserRead:
    """Get a user by id (admin only)."""
    return await UserService.get(db, user_id)


@router.patch("/me", response_model=UserRead)
async def update_me(
    data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    """Update current user's profile."""
    return await UserService.update_profile(db, current_user.id, data)


@router.post("/{user_id}/deactivate", status_code=status.HTTP_200_OK, dependencies=[role_checker])
async def deactivate_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> JSONResponse:
    """Deactivate (soft) a user account (admin only)."""
    await UserService.deactivate(db, user_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "User deactivated successfully."},
    )


@router.post("/{user_id}/activate", status_code=status.HTTP_200_OK, dependencies=[role_checker])
async def activate_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> JSONResponse:
    """Activate a previously deactivated user (admin only)."""
    await UserService.activate(db, user_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "User activated successfully."},
    )


@router.post("/{user_id}/role", status_code=status.HTTP_200_OK, dependencies=[role_checker])
async def set_user_role(
    user_id: UUID,
    data: UserRoleUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> JSONResponse:
    """Set a user's role (admin only)."""
    await UserService.set_role(db, user_id, data.role)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "User role updated successfully."},
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[role_checker])
async def delete_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete a user (admin only). Returns 204 on success."""
    await UserService.delete(db, user_id)


@router.get("/{user_id}/addresses", response_model=Page[AddressRead], dependencies=[role_checker])
async def list_user_addresses(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Page[AddressRead]:
    """Admin list addresses for any user."""
    items, total = await AddressService.list(db, user_id, offset=offset, limit=limit)
    return Page[AddressRead](items=items, total=total, limit=limit, offset=offset)

# mypy: disable-error-code=return-value
"""API routes for category endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import RoleChecker
from app.core.enums import UserRole
from app.db.session import get_session
from app.schemas.base import Page
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])
role_checker = Depends(RoleChecker([UserRole.ADMIN]))


@router.get("/", response_model=Page[CategoryRead])
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    search: str | None = Query(None, description="Search by name (case-insensitive)"),
    include_inactive: bool = Query(False, description="Include inactive categories in results"),
) -> Page[CategoryRead]:
    """List all categories."""
    categories, total = await CategoryService.list(
        db, limit=limit, offset=offset, search=search, include_inactive=include_inactive
    )
    return Page[CategoryRead](items=categories, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[role_checker],
)
async def create_category(
    data: CategoryCreate, db: Annotated[AsyncSession, Depends(get_session)]
) -> CategoryRead:
    """Create a new category."""
    return await CategoryService.create(data, db)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: UUID, db: Annotated[AsyncSession, Depends(get_session)]
) -> CategoryRead:
    """Get a category by ID."""
    return await CategoryService.get(category_id, db)


@router.patch("/{category_id}", response_model=CategoryRead, dependencies=[role_checker])
async def update_category(
    category_id: UUID, data: CategoryUpdate, db: Annotated[AsyncSession, Depends(get_session)]
) -> CategoryRead:
    """Update a category by ID."""
    return await CategoryService.update(category_id, data, db)


@router.delete(
    "/{category_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[role_checker]
)
async def delete_category(
    category_id: UUID, db: Annotated[AsyncSession, Depends(get_session)]
) -> None:
    """Delete a category by ID."""
    await CategoryService.delete(category_id, db)

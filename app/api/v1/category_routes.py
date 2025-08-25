# mypy: disable-error-code=return-value
"""API routes for category endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import Page
from app.services.category_service import CategoryService

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


@router.get("/", response_model=Page[CategoryRead])
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    search: str | None = Query(None, description="Search by name (case-insensitive)"),
) -> Page[CategoryRead]:
    """List all categories."""
    categories, total = await CategoryService.list(db, limit=limit, offset=offset, search=search)
    return Page[CategoryRead](items=categories, total=total, limit=limit, offset=offset)


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
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


@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: UUID, data: CategoryUpdate, db: Annotated[AsyncSession, Depends(get_session)]
) -> CategoryRead:
    """Update a category by ID."""
    return await CategoryService.update(category_id, data, db)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID, db: Annotated[AsyncSession, Depends(get_session)]
) -> None:
    """Delete a category by ID."""
    await CategoryService.delete(category_id, db)

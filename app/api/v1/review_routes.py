"""API routes for review endpoints."""

# mypy: disable-error-code=return-value
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import RoleChecker, get_current_user
from app.core.errors import NotFoundError
from app.db.session import get_session
from app.models.user import User
from app.schemas.common import Page
from app.schemas.review import (
    ReviewAdminUpdate,
    ReviewCreate,
    ReviewRead,
    ReviewUpdate,
)
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api/v1", tags=["Reviews"])
admin_checker = Depends(RoleChecker(["admin"]))


@router.post(
    "/products/{product_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    product_id: UUID,
    data: ReviewCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReviewRead:
    """Create a review for a product."""
    return await ReviewService.create(product_id, current_user.id, data, db)


@router.get("/products/{product_id}/reviews", response_model=Page[ReviewRead])
async def list_product_reviews(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    order_by: Literal["created_at", "rating"] = Query("created_at"),
    order_dir: Literal["asc", "desc"] = Query("desc"),
) -> Page[ReviewRead]:
    """List visible reviews for a product. Admin can see all via separate endpoint if needed."""
    is_admin = current_user is not None and current_user.role == "admin"
    items, total = await ReviewService.list(
        db,
        product_id=product_id,
        limit=limit,
        offset=offset,
        visible_only=not is_admin,  # admin sees all
        order_by=order_by,
        order_dir=order_dir,
    )
    return Page[ReviewRead](items=items, total=total, limit=limit, offset=offset)


@router.get("/reviews/{review_id}", response_model=ReviewRead)
async def get_review(
    review_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReviewRead:
    """Get a single review; invisible reviews only accessible by author or admin."""
    review = await ReviewService.get(review_id, db)
    if not review.is_visible and (
        current_user.id != review.user_id and current_user.role != "admin"
    ):
        raise NotFoundError("Review not found.")
    return review


@router.put("/reviews/{review_id}", response_model=ReviewRead)
async def update_review(
    review_id: UUID,
    data: ReviewUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReviewRead:
    """Update a review (author or admin)."""
    return await ReviewService.update(review_id, current_user.id, data, db)


@router.patch(
    "/reviews/{review_id}/visibility",
    response_model=ReviewRead,
    dependencies=[admin_checker],
)
async def moderate_review_visibility(
    review_id: UUID,
    data: ReviewAdminUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ReviewRead:
    """Toggle review visibility (admin only)."""
    return await ReviewService.set_visibility(review_id, data.is_visible, db)


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_review(
    review_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a review (author or admin)."""
    await ReviewService.delete(review_id, current_user.id, db)

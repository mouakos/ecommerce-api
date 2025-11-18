"""Service layer for review-related business logic."""

from typing import Literal
from uuid import UUID

from sqlmodel import asc, desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import (
    InsufficientPermissionError,
    ReviewNotFoundError,
    UserReviewProductAlreadyExistsError,
)
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.product_service import ProductService

OrderBy = Literal["created_at", "rating"]
OrderDir = Literal["asc", "desc"]


class ReviewService:
    """Service for managing reviews."""

    @staticmethod
    async def create(
        product_id: UUID, user_id: UUID, data: ReviewCreate, db: AsyncSession
    ) -> Review:
        """Create a new review for a product.

        Args:
            product_id (UUID): Product ID
            user_id (UUID): User ID
            data (ReviewCreate): Data for the new review
            db (AsyncSession): Database session

        Raises:
            NotFoundError: If the product does not exist
            ConflictError: If the user has already reviewed the product

        Returns:
            Review: The created review
        """
        # Ensure product exists
        _ = await ProductService.get(product_id, db)

        # Enforce one review per user & product
        existing = await db.exec(
            select(Review).where(Review.product_id == product_id).where(Review.user_id == user_id)
        )
        if existing.first():
            raise UserReviewProductAlreadyExistsError()

        review = Review(product_id=product_id, user_id=user_id, **data.model_dump())
        db.add(review)
        await db.flush()
        await db.refresh(review)
        return review

    @staticmethod
    async def list(
        db: AsyncSession,
        product_id: UUID,
        limit: int,
        offset: int,
        visible_only: bool = True,
        order_by: OrderBy = "created_at",
        order_dir: OrderDir = "desc",
    ) -> tuple[list[Review], int]:
        """List reviews for a product with pagination.

        Args:
            db (AsyncSession): Database session.
            product_id (UUID): Product ID.
            limit (int): Number of reviews to return.
            offset (int): Number of reviews to skip.
            visible_only (bool): Whether to return only visible reviews.
            order_by (OrderBy): Field to order by.
            order_dir (OrderDir): Direction to order (ascending or descending).

        Returns:
            tuple[list[Review], int]: List of reviews and total count.
        """
        stmt = select(Review).where(Review.product_id == product_id)
        count_stmt = select(func.count()).select_from(Review).where(Review.product_id == product_id)

        if visible_only:
            stmt = stmt.where(Review.is_visible)
            count_stmt = count_stmt.where(Review.is_visible)

        order_col = {"created_at": Review.created_at, "rating": Review.rating}[order_by]
        order_col = desc(order_col) if order_dir == "desc" else asc(order_col)

        total = (await db.exec(count_stmt)).one()
        res = await db.exec(stmt.order_by(order_col).limit(limit).offset(offset))
        items = list(res.all())
        return items, total

    @staticmethod
    async def get(review_id: UUID, db: AsyncSession) -> Review:
        """Get a review by ID.

        Args:
            review_id (UUID): Review ID.
            db (AsyncSession): Database session.

        Raises:
            NotFoundError: If the review does not exist.

        Returns:
            Review: The requested review.
        """
        review = await db.get(Review, review_id)
        if not review:
            raise ReviewNotFoundError()
        return review

    @staticmethod
    async def update(
        review_id: UUID,
        user_id: UUID,
        data: ReviewUpdate,
        db: AsyncSession,
    ) -> Review:
        """Update a review (author or admin).

        Args:
            review_id (UUID): Review ID.
            user_id (UUID): ID of the user attempting the update.
            data (ReviewUpdate): Data to update.
            is_admin (bool): Whether the user is an admin.
            db (AsyncSession): Database session.

        Raises:
            NotFoundError: If the review does not exist.
            UnauthorizedError: If the user is not allowed to update the review.
        """
        review = await db.get(Review, review_id)
        if not review:
            raise ReviewNotFoundError()
        if review.user_id != user_id and not review.user.role == "admin":
            raise InsufficientPermissionError()

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(review, key, value)
        await db.flush()
        await db.refresh(review)
        return review

    @staticmethod
    async def set_visibility(review_id: UUID, is_visible: bool, db: AsyncSession) -> Review:
        """Moderate review visibility (admin only).

        Args:
            review_id (UUID): Review ID.
            is_visible (bool): New visibility status.
            db (AsyncSession): Database session.

        Raises:
            NotFoundError: If the review does not exist.

        Returns:
            Review: The updated review.
        """
        review = await db.get(Review, review_id)
        if not review:
            raise ReviewNotFoundError()
        review.is_visible = is_visible
        await db.flush()
        await db.refresh(review)
        return review

    @staticmethod
    async def delete(review_id: UUID, user_id: UUID, db: AsyncSession) -> None:
        """Delete a review (author or admin).

        Args:
            review_id (UUID): Review ID.
            user_id (UUID): ID of the user attempting the deletion.
            db (AsyncSession): Database session.

        Raises:
            NotFoundError: If the review does not exist.
            UnauthorizedError: If the user is not allowed to delete the review.
        """
        review = await db.get(Review, review_id)
        if not review:
            raise ReviewNotFoundError()
        if review.user_id != user_id and not review.user.role == "admin":
            raise InsufficientPermissionError()
        await db.delete(review)
        await db.flush()

    @staticmethod
    async def average(product_id: UUID, db: AsyncSession) -> tuple[float | None, int]:
        """Compute average rating & count for visible reviews of a product.

        Args:
            product_id (UUID): Product ID.
            db (AsyncSession): Database session.

        Returns:
            tuple[float | None, int]: Average rating and count of visible reviews.
        """
        stmt = select(func.avg(Review.rating), func.count()).where(
            (Review.product_id == product_id) & (Review.is_visible.is_(True))  # type: ignore  [attr-defined]
        )
        avg_val, count_val = (await db.exec(stmt)).one()
        return (float(avg_val) if avg_val is not None else None, int(count_val))

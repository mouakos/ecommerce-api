"""Unit tests for ReviewService.

Cover create success, duplicate prevention, list visible vs all, update permission (author vs non-author),
delete permission, average rating calculation, set visibility, and not found cases.
"""

import uuid

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import (
    InsufficientPermissionError,
    ReviewNotFoundError,
    UserReviewProductAlreadyExistsError,
)
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.review_service import ReviewService


@pytest.mark.asyncio
async def test_create_review_success(
    db_session: AsyncSession, category_factory, product_factory, user_factory
):
    cat = await category_factory("Books")
    prod = await product_factory("Novel", category=cat)
    user = await user_factory("alice@example.com")
    review = await ReviewService.create(
        prod.id, user.id, ReviewCreate(rating=5, comment="Great"), db_session
    )
    assert review.id is not None
    assert review.rating == 5
    assert review.comment == "Great"
    assert review.product_id == prod.id and review.user_id == user.id


@pytest.mark.asyncio
async def test_create_review_duplicate_prevention(
    db_session: AsyncSession, category_factory, product_factory, user_factory
):
    cat = await category_factory("Tech")
    prod = await product_factory("Phone", category=cat)
    user = await user_factory("bob@example.com")
    await ReviewService.create(prod.id, user.id, ReviewCreate(rating=4, comment="Good"), db_session)
    with pytest.raises(UserReviewProductAlreadyExistsError):
        await ReviewService.create(
            prod.id, user.id, ReviewCreate(rating=3, comment="Ok"), db_session
        )


@pytest.mark.asyncio
async def test_list_reviews_visible_and_all(
    db_session: AsyncSession, category_factory, product_factory, user_factory
):
    cat = await category_factory("Clothes")
    prod = await product_factory("Shirt", category=cat)
    u1 = await user_factory("u1@example.com")
    u2 = await user_factory("u2@example.com")
    await ReviewService.create(prod.id, u1.id, ReviewCreate(rating=5, comment="Love"), db_session)
    r2 = await ReviewService.create(
        prod.id, u2.id, ReviewCreate(rating=2, comment="Bad"), db_session
    )
    # hide second
    await ReviewService.set_visibility(r2.id, False, db_session)

    visible_items, visible_total = await ReviewService.list(db_session, prod.id, limit=10, offset=0)
    assert visible_total == 1
    assert all(r.is_visible for r in visible_items)

    all_items, all_total = await ReviewService.list(
        db_session, prod.id, limit=10, offset=0, visible_only=False
    )
    assert all_total == 2
    assert any(not r.is_visible for r in all_items)


@pytest.mark.asyncio
async def test_update_review_author_success(
    db_session: AsyncSession, category_factory, product_factory, user_factory
):
    cat = await category_factory("Games")
    prod = await product_factory("Chess", category=cat)
    user = await user_factory("author@example.com")
    review = await ReviewService.create(
        prod.id, user.id, ReviewCreate(rating=3, comment="Ok"), db_session
    )
    updated = await ReviewService.update(
        review.id, user.id, ReviewUpdate(rating=4, comment="Better"), db_session
    )
    assert updated.rating == 4 and updated.comment == "Better"


@pytest.mark.asyncio
async def test_update_review_non_author_forbidden(
    db_session: AsyncSession, category_factory, product_factory, user_factory
):
    cat = await category_factory("Electronics")
    prod = await product_factory("Tablet", category=cat)
    author = await user_factory("auth@example.com")
    other = await user_factory("other@example.com")
    review = await ReviewService.create(
        prod.id, author.id, ReviewCreate(rating=2, comment="Meh"), db_session
    )
    with pytest.raises(InsufficientPermissionError):
        await ReviewService.update(review.id, other.id, ReviewUpdate(rating=5), db_session)


@pytest.mark.asyncio
async def test_delete_review_author_success(
    db_session: AsyncSession, category_factory, product_factory, user_factory
):
    cat = await category_factory("Office")
    prod = await product_factory("Chair", category=cat)
    user = await user_factory("del@example.com")
    review = await ReviewService.create(prod.id, user.id, ReviewCreate(rating=5), db_session)
    await ReviewService.delete(review.id, user.id, db_session)
    with pytest.raises(ReviewNotFoundError):
        await ReviewService.get(review.id, db_session)


@pytest.mark.asyncio
async def test_delete_review_non_author_forbidden(
    db_session: AsyncSession, category_factory, product_factory, user_factory
):
    cat = await category_factory("Garden")
    prod = await product_factory("Rake", category=cat)
    author = await user_factory("gardener@example.com")
    other = await user_factory("intruder@example.com")
    review = await ReviewService.create(prod.id, author.id, ReviewCreate(rating=1), db_session)
    with pytest.raises(InsufficientPermissionError):
        await ReviewService.delete(review.id, other.id, db_session)


@pytest.mark.asyncio
async def test_average_rating_only_visible(
    db_session: AsyncSession, category_factory, product_factory, user_factory
):
    cat = await category_factory("Music")
    prod = await product_factory("Guitar", category=cat)
    u1 = await user_factory("r1@example.com")
    u2 = await user_factory("r2@example.com")
    await ReviewService.create(prod.id, u1.id, ReviewCreate(rating=5), db_session)
    r2 = await ReviewService.create(prod.id, u2.id, ReviewCreate(rating=1), db_session)
    # hide low rating
    await ReviewService.set_visibility(r2.id, False, db_session)
    avg, count = await ReviewService.average(prod.id, db_session)
    assert avg == 5.0 and count == 1


@pytest.mark.asyncio
async def test_get_review_not_found(db_session: AsyncSession):
    with pytest.raises(ReviewNotFoundError):
        await ReviewService.get(uuid.uuid4(), db_session)

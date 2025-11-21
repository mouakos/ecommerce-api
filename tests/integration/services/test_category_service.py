"""Unit tests for CategoryService logic.

Cover: create, duplicate prevention, list with search, get not found, update name conflict,
successful update, delete success & delete not found.
"""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import CategoryAlreadyExistsError, CategoryNotFoundError
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.category_service import CategoryService


@pytest.mark.asyncio
async def test_create_category_success(db_session: AsyncSession):
    cat = await CategoryService.create(CategoryCreate(name="Books"), db_session)
    assert cat.id is not None
    assert cat.name == "Books"


@pytest.mark.asyncio
async def test_create_category_duplicate(db_session: AsyncSession):
    await CategoryService.create(CategoryCreate(name="Electronics"), db_session)
    with pytest.raises(CategoryAlreadyExistsError):
        await CategoryService.create(CategoryCreate(name="Electronics"), db_session)


@pytest.mark.asyncio
async def test_list_categories_with_search(db_session: AsyncSession):
    for name in ["Shoes", "Shirts", "Pants"]:
        await CategoryService.create(CategoryCreate(name=name), db_session)
    # Create an inactive category that should not appear by default
    inactive = await CategoryService.create(CategoryCreate(name="Hidden"), db_session)
    inactive.is_active = False
    await db_session.flush()

    items, total = await CategoryService.list(db_session, limit=10, offset=0, search="sh")
    assert total >= 2  # at least Shoes & Shirts
    names = {c.name for c in items}
    assert "Shoes" in names
    assert "Shirts" in names
    assert "Hidden" not in names

    # When including inactive, Hidden should appear if it matches search
    items_with_inactive, total_with_inactive = await CategoryService.list(
        db_session, limit=10, offset=0, search="hid", include_inactive=True
    )
    names2 = {c.name for c in items_with_inactive}
    assert "Hidden" in names2


@pytest.mark.asyncio
async def test_get_category_not_found(db_session: AsyncSession):
    import uuid

    with pytest.raises(CategoryNotFoundError):
        await CategoryService.get(uuid.uuid4(), db_session)


@pytest.mark.asyncio
async def test_update_category_success(db_session: AsyncSession):
    cat = await CategoryService.create(CategoryCreate(name="Home"), db_session)
    updated = await CategoryService.update(cat.id, CategoryUpdate(name="Home & Garden"), db_session)
    assert updated.name == "Home & Garden"


@pytest.mark.asyncio
async def test_update_category_name_conflict(db_session: AsyncSession):
    await CategoryService.create(CategoryCreate(name="Toys"), db_session)
    cat2 = await CategoryService.create(CategoryCreate(name="Games"), db_session)
    with pytest.raises(CategoryAlreadyExistsError):
        await CategoryService.update(cat2.id, CategoryUpdate(name="Toys"), db_session)
    # Ensure original name unchanged
    unchanged = await CategoryService.get(cat2.id, db_session)
    assert unchanged.name == "Games"


@pytest.mark.asyncio
async def test_delete_category_success(db_session: AsyncSession):
    cat = await CategoryService.create(CategoryCreate(name="Office"), db_session)
    await CategoryService.delete(cat.id, db_session)
    with pytest.raises(CategoryNotFoundError):
        await CategoryService.get(cat.id, db_session)


@pytest.mark.asyncio
async def test_delete_category_not_found(db_session: AsyncSession):
    import uuid

    with pytest.raises(CategoryNotFoundError):
        await CategoryService.delete(uuid.uuid4(), db_session)

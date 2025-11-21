"""Unit tests for ProductService.

Cover create success, duplicate within same category, list filters/search, get not found,
update success (including category change & duplicate name prevention), delete success & not found.
"""

import uuid

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import ProductAlreadyExistsError, ProductNotFoundError
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product_service import ProductService


@pytest.mark.asyncio
async def test_create_product_success(db_session: AsyncSession, category_factory):
    cat = await category_factory("Books")
    prod = await ProductService.create(
        ProductCreate(name="Novel", description="Story", price=12.5, stock=10, category_id=cat.id),
        db_session,
    )
    assert prod.id is not None
    assert prod.name == "Novel"
    assert prod.category_id == cat.id


@pytest.mark.asyncio
async def test_create_product_duplicate_name_same_category(
    db_session: AsyncSession, category_factory
):
    cat = await category_factory("Electronics")
    await ProductService.create(
        ProductCreate(name="Phone", description=None, price=299.0, stock=5, category_id=cat.id),
        db_session,
    )
    with pytest.raises(ProductAlreadyExistsError):
        await ProductService.create(
            ProductCreate(
                name="Phone", description="Smart", price=310.0, stock=7, category_id=cat.id
            ),
            db_session,
        )


@pytest.mark.asyncio
async def test_list_products_with_search_and_filters(db_session: AsyncSession, category_factory):
    cat = await category_factory("Clothes")
    names = ["Red Shirt", "Blue Shirt", "Green Pants", "Socks"]
    prices = [15.0, 17.0, 25.0, 5.0]
    stocks = [10, 0, 3, 20]
    for n, p, s in zip(names, prices, stocks, strict=True):
        await ProductService.create(
            ProductCreate(name=n, description=n.lower(), price=p, stock=s, category_id=cat.id),
            db_session,
        )

    # Create an unavailable product matching search that should be hidden by default
    unavailable = await ProductService.create(
        ProductCreate(
            name="Hidden Shirt",
            description="hidden shirt",
            price=11.0,
            stock=5,
            category_id=cat.id,
            is_available=True,
        ),
        db_session,
    )
    # toggle availability off
    unavailable.is_available = False
    await db_session.flush()

    # search "shirt" should match Red/Blue Shirt
    items, total = await ProductService.list(db_session, limit=10, offset=0, search="shirt")
    assert total >= 2
    matched_names = {i.name for i in items}
    assert "Red Shirt" in matched_names and "Blue Shirt" in matched_names
    assert "Hidden Shirt" not in matched_names

    # in_stock True should exclude Blue Shirt (stock 0)
    in_stock_items, _ = await ProductService.list(db_session, limit=10, offset=0, in_stock=True)
    in_stock_names = {i.name for i in in_stock_items}
    assert "Blue Shirt" not in in_stock_names

    # price_min filter
    expensive_items, _ = await ProductService.list(db_session, limit=10, offset=0, price_min=20)
    assert all(i.price >= 20 for i in expensive_items)

    # Include unavailable to fetch hidden shirt via search
    items_with_unavailable, _ = await ProductService.list(
        db_session, limit=10, offset=0, search="hidden", include_unavailable=True
    )
    assert any(i.name == "Hidden Shirt" for i in items_with_unavailable)


@pytest.mark.asyncio
async def test_get_product_not_found(db_session: AsyncSession):
    with pytest.raises(ProductNotFoundError):
        await ProductService.get(uuid.uuid4(), db_session)


@pytest.mark.asyncio
async def test_update_product_success_and_category_change(
    db_session: AsyncSession, category_factory
):
    cat1 = await category_factory("Games")
    cat2 = await category_factory("GamesAlt")
    prod = await ProductService.create(
        ProductCreate(
            name="Board", description="Board game", price=30.0, stock=4, category_id=cat1.id
        ),
        db_session,
    )
    updated = await ProductService.update(
        prod.id,
        ProductUpdate(name="Board Deluxe", price=35.0, category_id=cat2.id),
        db_session,
    )
    assert updated.name == "Board Deluxe"
    assert updated.price == 35.0
    assert updated.category_id == cat2.id


@pytest.mark.asyncio
async def test_update_product_duplicate_name_in_target_category(
    db_session: AsyncSession, category_factory
):
    cat = await category_factory("Tech")
    await ProductService.create(
        ProductCreate(name="Laptop", description=None, price=900.0, stock=3, category_id=cat.id),
        db_session,
    )
    p_tablet = await ProductService.create(
        ProductCreate(name="Tablet", description=None, price=500.0, stock=6, category_id=cat.id),
        db_session,
    )
    # attempt rename second product to existing name in same category — should raise
    with pytest.raises(ProductAlreadyExistsError):
        await ProductService.update(
            p_tablet.id,
            ProductUpdate(name="Laptop"),
            db_session,
        )


@pytest.mark.asyncio
async def test_delete_product_success_and_not_found(db_session: AsyncSession, category_factory):
    cat = await category_factory("Office")
    prod = await ProductService.create(
        ProductCreate(name="Chair", description="Seat", price=45.0, stock=10, category_id=cat.id),
        db_session,
    )
    await ProductService.delete(prod.id, db_session)
    with pytest.raises(ProductNotFoundError):
        await ProductService.get(prod.id, db_session)
    # deleting again should raise
    with pytest.raises(ProductNotFoundError):
        await ProductService.delete(prod.id, db_session)

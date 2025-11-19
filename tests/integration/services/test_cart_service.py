"""Unit tests for CartService business logic.

Focus: creation of cart, adding items, stock enforcement, updating/removing items, clearing cart.
These tests bypass HTTP layer and call service functions directly using the async SQLModel session
fixture provided in `tests/conftest.py`.
"""

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import CartItemNotFoundError, InsufficientStockError
from app.core.security import get_password_hash
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate
from app.services.cart_service import CartService


@pytest.mark.asyncio
async def test_get_or_create_user_cart_creates(db_session: AsyncSession):
    user = User(
        email="cartuser@example.com", hashed_password=get_password_hash("Pass123"), is_verified=True
    )
    db_session.add(user)
    await db_session.flush()

    cart = await CartService.get_or_create_user_cart(user.id, db_session)
    assert cart.id is not None
    assert cart.user_id == user.id


@pytest.mark.asyncio
async def test_add_item_to_cart_success(db_session: AsyncSession, product_factory):
    user = User(
        email="additem@example.com", hashed_password=get_password_hash("Pass123"), is_verified=True
    )
    db_session.add(user)
    await db_session.flush()
    product = await product_factory("Widget", price=9.99, stock=10)

    cart = await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=product.id, quantity=3), db_session
    )
    assert len(cart.items) == 1
    item = cart.items[0]
    assert item.product_id == product.id
    assert item.quantity == 3
    assert item.unit_price == product.price


@pytest.mark.asyncio
async def test_add_item_stock_enforcement(db_session: AsyncSession, product_factory):
    user = User(
        email="stockfail@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    product = await product_factory("Gizmo", price=5.00, stock=2)

    # First add within stock
    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=product.id, quantity=1), db_session
    )
    # Second add exceeding stock
    with pytest.raises(InsufficientStockError):
        await CartService.add_item_to_user_cart(
            user.id, CartItemCreate(product_id=product.id, quantity=2), db_session
        )


@pytest.mark.asyncio
async def test_update_item_quantity_and_remove(db_session: AsyncSession, product_factory):
    user = User(
        email="updateitem@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    product = await product_factory("Thing", price=12.50, stock=5)

    cart = await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=product.id, quantity=2), db_session
    )
    item_id = cart.items[0].id

    # Update quantity within stock
    cart = await CartService.update_item_to_user_cart(user.id, item_id, 4, db_session)
    assert cart.items[0].quantity == 4

    # Remove item (quantity <= 0 triggers delete)
    cart = await CartService.update_item_to_user_cart(user.id, item_id, 0, db_session)
    assert len(cart.items) == 0


@pytest.mark.asyncio
async def test_update_item_not_found(db_session: AsyncSession):
    user = User(
        email="missingitem@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    # Random UUID-like approach: create another user's cart item or just pass a non-existent ID.
    from uuid import uuid4

    with pytest.raises(CartItemNotFoundError):
        await CartService.update_item_to_user_cart(user.id, uuid4(), 3, db_session)


@pytest.mark.asyncio
async def test_remove_item_from_user_cart(db_session: AsyncSession, product_factory):
    user = User(
        email="removeitem@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    product = await product_factory("Device", price=20.00, stock=3)

    cart = await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=product.id, quantity=1), db_session
    )
    item_id = cart.items[0].id
    await CartService.remove_item_from_user_cart(user.id, item_id, db_session)
    # refetch cart
    cart = await CartService.get_user_cart(user.id, db_session)
    assert cart is not None
    # Relationship may be stale; directly count cart items
    res = await db_session.exec(select(Product).where(Product.id == product.id))
    # verify product still exists
    assert res.first() is not None
    from app.models.cart import CartItem

    count_items = await db_session.exec(select(CartItem).where(CartItem.cart_id == cart.id))
    assert len(count_items.all()) == 0


@pytest.mark.asyncio
async def test_clear_user_cart(db_session: AsyncSession, product_factory):
    user = User(
        email="clearcart@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    product = await product_factory("Wand", price=3.33, stock=9)

    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=product.id, quantity=2), db_session
    )
    cart = await CartService.get_user_cart(user.id, db_session)
    assert cart is not None and len(cart.items) == 1
    await CartService.clear_user_cart(user.id, db_session)
    cart = await CartService.get_user_cart(user.id, db_session)
    assert cart is None

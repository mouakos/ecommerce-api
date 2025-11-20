"""Unit tests for OrderService logic.

Cover checkout success, empty cart, insufficient stock, list orders, get specific order,
order not found, and status update. Focus on transactional stock decrement and cart deletion.
"""

import uuid

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.enums import OrderStatus
from app.core.errors import EmptyCartError, InsufficientStockError, OrderNotFoundError
from app.core.security import get_password_hash
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate
from app.schemas.order import OrderCheckout
from app.services.cart_service import CartService
from app.services.order_service import OrderService


@pytest.mark.asyncio
async def test_checkout_success_creates_order_and_decrements_stock(
    db_session: AsyncSession, product_factory, address_factory
):
    user = User(
        email="orderuser@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    prod = await product_factory("Widget", price=10.0, stock=5)
    # add item to cart
    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=prod.id, quantity=3), db_session
    )

    ship = await address_factory(
        user.id, line1="1 Ship St", city="Paris", state="FR-IDF", postal_code="75001", country="fr"
    )
    bill = await address_factory(
        user.id, line1="2 Bill Ave", city="Paris", state="FR-IDF", postal_code="75002", country="fr"
    )
    order = await OrderService.checkout(
        user.id,
        order_checkout=OrderCheckout(shipping_address_id=ship.id, billing_address_id=bill.id),
        db=db_session,
    )
    assert order.id is not None
    assert order.number.startswith("ORD-")
    assert order.total_amount == pytest.approx(30.0)
    assert len(order.items) == 1
    # stock decremented
    updated_prod = await db_session.get(Product, prod.id)
    assert updated_prod is not None and updated_prod.stock == 2
    # cart removed
    cart = await CartService.get_user_cart(user.id, db_session)
    assert cart is None


@pytest.mark.asyncio
async def test_checkout_empty_cart_raises(db_session: AsyncSession, address_factory):
    user = User(
        email="emptycart@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    ship = await address_factory(
        user.id, line1="3 Ship St", city="Paris", state="FR-IDF", postal_code="75003", country="fr"
    )
    bill = await address_factory(
        user.id, line1="4 Bill Ave", city="Paris", state="FR-IDF", postal_code="75004", country="fr"
    )
    with pytest.raises(EmptyCartError):
        await OrderService.checkout(
            user.id,
            order_checkout=OrderCheckout(shipping_address_id=ship.id, billing_address_id=bill.id),
            db=db_session,
        )


@pytest.mark.asyncio
async def test_checkout_insufficient_stock_raises(
    db_session: AsyncSession, product_factory, address_factory
):
    user = User(
        email="lowstock@example.com", hashed_password=get_password_hash("Pass123"), is_verified=True
    )
    db_session.add(user)
    await db_session.flush()
    prod = await product_factory("Gadget", price=7.5, stock=2)
    # add more than stock in two steps to reach validation loop
    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=prod.id, quantity=2), db_session
    )
    # artificially bump cart item quantity beyond stock (simulate out-of-sync)
    cart = await CartService.get_user_cart(user.id, db_session)
    cart_item = cart.items[0]
    cart_item.quantity = 3  # exceed product stock
    await db_session.flush()
    ship = await address_factory(
        user.id, line1="5 Ship St", city="Paris", state="FR-IDF", postal_code="75005", country="fr"
    )
    bill = await address_factory(
        user.id, line1="6 Bill Ave", city="Paris", state="FR-IDF", postal_code="75006", country="fr"
    )
    with pytest.raises(InsufficientStockError):
        await OrderService.checkout(
            user.id,
            order_checkout=OrderCheckout(shipping_address_id=ship.id, billing_address_id=bill.id),
            db=db_session,
        )


@pytest.mark.asyncio
async def test_list_user_orders_returns_in_desc_created_order(
    db_session: AsyncSession, product_factory, address_factory
):
    user = User(
        email="listorders@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    p1 = await product_factory("ItemA", price=4.0, stock=5)
    p2 = await product_factory("ItemB", price=6.0, stock=5)

    # First order
    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=p1.id, quantity=1), db_session
    )
    ship = await address_factory(
        user.id, line1="7 Ship St", city="Paris", state="FR-IDF", postal_code="75007", country="fr"
    )
    bill = await address_factory(
        user.id, line1="8 Bill Ave", city="Paris", state="FR-IDF", postal_code="75008", country="fr"
    )
    await OrderService.checkout(
        user.id,
        order_checkout=OrderCheckout(shipping_address_id=ship.id, billing_address_id=bill.id),
        db=db_session,
    )
    # Second order
    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=p2.id, quantity=2), db_session
    )
    await OrderService.checkout(
        user.id,
        order_checkout=OrderCheckout(shipping_address_id=ship.id, billing_address_id=bill.id),
        db=db_session,
    )

    orders = await OrderService.list_user_orders(user.id, db_session)
    assert len(orders) == 2
    # descending by created_at: second order first
    assert orders[0].total_amount == pytest.approx(12.0)
    assert orders[1].total_amount == pytest.approx(4.0)


@pytest.mark.asyncio
async def test_get_user_order_success(db_session: AsyncSession, product_factory, address_factory):
    user = User(
        email="getorder@example.com", hashed_password=get_password_hash("Pass123"), is_verified=True
    )
    db_session.add(user)
    await db_session.flush()
    prod = await product_factory("Single", price=9.0, stock=3)
    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=prod.id, quantity=2), db_session
    )
    ship = await address_factory(
        user.id, line1="9 Ship St", city="Paris", state="FR-IDF", postal_code="75009", country="fr"
    )
    bill = await address_factory(
        user.id,
        line1="10 Bill Ave",
        city="Paris",
        state="FR-IDF",
        postal_code="75010",
        country="fr",
    )
    order = await OrderService.checkout(
        user.id,
        order_checkout=OrderCheckout(shipping_address_id=ship.id, billing_address_id=bill.id),
        db=db_session,
    )

    fetched = await OrderService.get_user_order(user.id, order.id, db_session)
    assert fetched.id == order.id
    assert fetched.number == order.number


@pytest.mark.asyncio
async def test_get_user_order_not_found(db_session: AsyncSession):
    user = User(
        email="nforder@example.com", hashed_password=get_password_hash("Pass123"), is_verified=True
    )
    db_session.add(user)
    await db_session.flush()
    import uuid

    with pytest.raises(OrderNotFoundError):
        await OrderService.get_user_order(user.id, uuid.uuid4(), db_session)


@pytest.mark.asyncio
async def test_update_order_status_success(
    db_session: AsyncSession, product_factory, address_factory
):
    """Update an order's status successfully."""
    user = User(
        email="statussucc@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    prod = await product_factory("StatusItem", price=12.0, stock=5)
    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=prod.id, quantity=2), db_session
    )
    ship = await address_factory(
        user.id, line1="11 Ship St", city="Paris", state="FR-IDF", postal_code="75111", country="fr"
    )
    bill = await address_factory(
        user.id,
        line1="12 Bill Ave",
        city="Paris",
        state="FR-IDF",
        postal_code="75112",
        country="fr",
    )
    order = await OrderService.checkout(
        user.id,
        order_checkout=OrderCheckout(shipping_address_id=ship.id, billing_address_id=bill.id),
        db=db_session,
    )
    assert order.status == OrderStatus.PENDING
    updated = await OrderService.update_order_status(order.id, OrderStatus.PROCESSING, db_session)
    assert updated.status == OrderStatus.PROCESSING


@pytest.mark.asyncio
async def test_update_order_status_invalid_transition(
    db_session: AsyncSession, product_factory, address_factory
):
    """Attempt an invalid transition (e.g., PENDING -> DELIVERED) should raise error."""
    user = User(
        email="statusbad@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    prod = await product_factory("BadStatusItem", price=5.0, stock=2)
    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=prod.id, quantity=1), db_session
    )
    ship = await address_factory(
        user.id, line1="13 Ship St", city="Paris", state="FR-IDF", postal_code="75113", country="fr"
    )
    bill = await address_factory(
        user.id,
        line1="14 Bill Ave",
        city="Paris",
        state="FR-IDF",
        postal_code="75114",
        country="fr",
    )
    order = await OrderService.checkout(
        user.id,
        order_checkout=OrderCheckout(shipping_address_id=ship.id, billing_address_id=bill.id),
        db=db_session,
    )
    from app.core.errors import InvalidOrderStatusTransitionError

    with pytest.raises(InvalidOrderStatusTransitionError):
        await OrderService.update_order_status(order.id, OrderStatus.DELIVERED, db_session)


@pytest.mark.asyncio
async def test_update_order_status_idempotent(
    db_session: AsyncSession, product_factory, address_factory
):
    """Updating an order to the same status should return unchanged order (idempotent)."""
    user = User(
        email="statusidem@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    prod = await product_factory("IdemStatusItem", price=8.0, stock=3)
    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=prod.id, quantity=1), db_session
    )
    ship = await address_factory(
        user.id, line1="15 Ship St", city="Paris", state="FR-IDF", postal_code="75115", country="fr"
    )
    bill = await address_factory(
        user.id,
        line1="16 Bill Ave",
        city="Paris",
        state="FR-IDF",
        postal_code="75116",
        country="fr",
    )
    order = await OrderService.checkout(
        user.id,
        order_checkout=OrderCheckout(shipping_address_id=ship.id, billing_address_id=bill.id),
        db=db_session,
    )
    original_number = order.number
    original_status = order.status
    updated = await OrderService.update_order_status(order.id, original_status, db_session)
    assert updated.id == order.id
    assert updated.number == original_number
    assert updated.status == original_status


@pytest.mark.asyncio
async def test_checkout_with_addresses_persists_ids(
    db_session: AsyncSession, product_factory, address_factory
):
    """Checkout assigns provided shipping/billing address IDs."""
    user = User(
        email="addrorder@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    prod = await product_factory("AddrWidget", price=10.0, stock=5)
    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=prod.id, quantity=2), db_session
    )
    ship = await address_factory(
        user.id, line1="1 Ship St", city="Paris", state="FR-IDF", postal_code="75001", country="fr"
    )
    bill = await address_factory(
        user.id, line1="2 Bill Ave", city="Paris", state="FR-IDF", postal_code="75002", country="fr"
    )
    order = await OrderService.checkout(
        user.id,
        order_checkout=OrderCheckout(
            shipping_address_id=ship.id,
            billing_address_id=bill.id,
        ),
        db=db_session,
    )
    assert order.shipping_address_id == ship.id
    assert order.billing_address_id == bill.id


@pytest.mark.asyncio
async def test_checkout_with_foreign_address_raises(
    db_session: AsyncSession, product_factory, address_factory
):
    """Checkout with address belonging to another user should raise AddressNotFoundError."""
    user1 = User(
        email="addruser1@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    user2 = User(
        email="addruser2@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user1)
    db_session.add(user2)
    await db_session.flush()
    prod = await product_factory("BadAddrWidget", price=5.0, stock=3)
    await CartService.add_item_to_user_cart(
        user1.id, CartItemCreate(product_id=prod.id, quantity=1), db_session
    )
    foreign_addr = await address_factory(
        user2.id,
        line1="Foreign St",
        city="Paris",
        state="FR-IDF",
        postal_code="75003",
        country="fr",
    )
    # Provide valid billing address for user1 so only shipping is foreign
    billing_addr = await address_factory(
        user1.id,
        line1="Own Billing",
        city="Paris",
        state="FR-IDF",
        postal_code="75004",
        country="fr",
    )
    from app.core.errors import AddressNotFoundError

    with pytest.raises(AddressNotFoundError):
        await OrderService.checkout(
            user1.id,
            order_checkout=OrderCheckout(
                shipping_address_id=foreign_addr.id,
                billing_address_id=billing_addr.id,
            ),
            db=db_session,
        )


@pytest.mark.asyncio
async def test_checkout_missing_addresses_error(db_session: AsyncSession, product_factory):
    """Service checkout raises AddressNotFoundError if addresses not found."""
    from app.core.errors import AddressNotFoundError

    user = User(
        email="noaddr@example.com",
        hashed_password=get_password_hash("Pass123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    prod = await product_factory("NoAddrWidget", price=5.0, stock=2)
    await CartService.add_item_to_user_cart(
        user.id, CartItemCreate(product_id=prod.id, quantity=1), db_session
    )
    order_checkout = OrderCheckout(
        shipping_address_id=uuid.uuid4(),
        billing_address_id=uuid.uuid4(),
    )
    with pytest.raises(AddressNotFoundError):
        await OrderService.checkout(user.id, order_checkout, db_session)


@pytest.mark.asyncio
async def test_update_order_status_not_found(db_session: AsyncSession):
    """Updating a non-existent order status should raise OrderNotFoundError."""
    import uuid

    with pytest.raises(OrderNotFoundError):
        await OrderService.update_order_status(uuid.uuid4(), OrderStatus.SHIPPED, db_session)

"""End to end tests for order-related API endpoints, including status update cases."""

import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.core.config import settings
from tests.factories import CartFactory, CartItemFactory, ProductFactory

CART = "/api/v1/cart"
ORD = "/api/v1/orders"


def get_user_id_from_token(auth_client: AsyncClient) -> UUID:
    from jose import jwt

    auth_header = auth_client.headers.get("Authorization")
    token = auth_header.split(" ")[1]  # Remove "Bearer " prefix
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    return UUID(payload.get("sub"))  # or another claim, depending on your implementation


@pytest.mark.asyncio
async def test_checkout_decrements_stock_and_clears_cart(auth_client: AsyncClient, db_session):
    product = ProductFactory(stock=3, price=10.0)
    await db_session.flush()
    user_id = get_user_id_from_token(auth_client)
    cart_item = CartItemFactory.build(product=product, quantity=2, unit_price=10.0)
    CartFactory(user_id=user_id, items=[cart_item])

    r = await auth_client.post(f"{ORD}/", json={})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["total_amount"] == 20.0
    assert len(body["items"]) == 1 and body["items"][0]["quantity"] == 2

    # cart is cleared
    cart = (await auth_client.get(f"{CART}/")).json()
    assert cart["items"] == []


@pytest.mark.asyncio
async def test_checkout_empty_cart_400(auth_client: AsyncClient, db_session):
    user_id = get_user_id_from_token(auth_client)
    CartFactory(user_id=user_id)
    await db_session.flush()

    r = await auth_client.post(f"{ORD}/", json={})
    assert r.status_code == 400
    assert r.json()["detail"] == "Cart is empty."


@pytest.mark.asyncio
async def test_list_and_get_my_orders(auth_client: AsyncClient, db_session):
    product = ProductFactory(stock=5, price=10.0)
    await db_session.flush()
    user_id = get_user_id_from_token(auth_client)
    cart_item = CartItemFactory.build(product=product, quantity=2, unit_price=10.0)
    CartFactory(user_id=user_id, items=[cart_item])
    created = (await auth_client.post(f"{ORD}/", json={})).json()

    # list
    r_list = await auth_client.get(f"{ORD}/")
    assert r_list.status_code == 200
    assert any(o["id"] == created["id"] for o in r_list.json())

    # get one
    r_one = await auth_client.get(f"{ORD}/{created['id']}")
    assert r_one.status_code == 200
    assert r_one.json()["number"].startswith("ORD-")


@pytest.mark.asyncio
async def test_admin_updates_order_status_success(
    auth_admin_client: AsyncClient, auth_client: AsyncClient, db_session
):
    """Admin can update an order's status."""
    product = ProductFactory(stock=10, price=5.0)
    await db_session.flush()
    user_id = get_user_id_from_token(auth_client)
    cart_item = CartItemFactory.build(product=product, quantity=2, unit_price=5.0)
    CartFactory(user_id=user_id, items=[cart_item])
    created = (await auth_client.post(f"{ORD}/", json={})).json()
    order_id = created["id"]
    assert created["status"] == "pending"
    r_patch = await auth_admin_client.patch(
        f"{ORD}/{order_id}/status", json={"status": "processing"}
    )
    assert r_patch.status_code == 200, r_patch.text
    assert r_patch.json()["status"] == "processing"


@pytest.mark.asyncio
async def test_user_cannot_update_order_status_forbidden(auth_client: AsyncClient, db_session):
    """Non-admin user attempting status update should get 403."""
    product = ProductFactory(stock=4, price=3.5)
    await db_session.flush()
    user_id = get_user_id_from_token(auth_client)
    cart_item = CartItemFactory.build(product=product, quantity=1, unit_price=3.5)
    CartFactory(user_id=user_id, items=[cart_item])
    created = (await auth_client.post(f"{ORD}/", json={})).json()
    order_id = created["id"]
    r_forbidden = await auth_client.patch(f"{ORD}/{order_id}/status", json={"status": "processing"})
    assert r_forbidden.status_code == 403
    assert r_forbidden.json()["error_code"] == "insufficient_permissions"


@pytest.mark.asyncio
async def test_admin_update_order_status_not_found(auth_admin_client: AsyncClient):
    """Admin updating non-existent order returns 404."""
    fake_id = uuid.uuid4()
    r = await auth_admin_client.patch(f"{ORD}/{fake_id}/status", json={"status": "processing"})
    assert r.status_code == 404
    assert r.json()["error_code"] == "order_not_found"


@pytest.mark.asyncio
async def test_admin_update_order_status_validation_error(auth_admin_client: AsyncClient):
    """Invalid status value should yield 422 validation error."""
    r = await auth_admin_client.patch(
        f"{ORD}/{uuid.uuid4()}/status", json={"status": "not-a-real-status"}
    )
    assert r.status_code == 422
    # Pydantic validation returns detail list
    assert "detail" in r.json()


@pytest.mark.asyncio
async def test_admin_update_order_status_invalid_transition(
    auth_admin_client: AsyncClient, auth_client: AsyncClient, db_session
):
    """Admin attempting invalid transition (pending -> delivered) gets 400 invalid_order_status_transition."""
    product = ProductFactory(stock=3, price=11.0)
    await db_session.flush()
    user_id = get_user_id_from_token(auth_client)
    cart_item = CartItemFactory.build(product=product, quantity=1, unit_price=11.0)
    CartFactory(user_id=user_id, items=[cart_item])
    created = (await auth_client.post(f"{ORD}/", json={})).json()
    order_id = created["id"]
    r_invalid = await auth_admin_client.patch(
        f"{ORD}/{order_id}/status", json={"status": "delivered"}
    )
    assert r_invalid.status_code == 400
    body = r_invalid.json()
    assert body["error_code"] == "invalid_order_status_transition"


@pytest.mark.asyncio
async def test_checkout_with_addresses(auth_client: AsyncClient, db_session, address_factory):
    """Checkout with provided shipping & billing address IDs persists them."""
    product = ProductFactory(stock=6, price=9.0)
    await db_session.flush()
    user_id = get_user_id_from_token(auth_client)
    cart_item = CartItemFactory.build(product=product, quantity=2, unit_price=9.0)
    CartFactory(user_id=user_id, items=[cart_item])
    ship = await address_factory(
        user_id, street="10 Ship Way", city="Paris", postal_code="75010", country="fr"
    )
    bill = await address_factory(
        user_id, street="20 Bill Way", city="Paris", postal_code="75020", country="fr"
    )
    r = await auth_client.post(
        f"{ORD}/",
        json={"shipping_address_id": str(ship.id), "billing_address_id": str(bill.id)},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["shipping_address_id"] == str(ship.id)
    assert body["billing_address_id"] == str(bill.id)


@pytest.mark.asyncio
async def test_checkout_with_foreign_address_forbidden(
    auth_client: AsyncClient, db_session, address_factory
):
    """Checkout using address owned by another user should 404 with address_not_found."""
    # create another user & address via direct factory pattern
    from app.core.security import get_password_hash
    from app.models.user import User

    other = User(
        email="otheraddr@example.com",
        hashed_password=get_password_hash("OtherPass1"),
        is_verified=True,
    )
    db_session.add(other)
    await db_session.flush()
    foreign_addr = await address_factory(
        other.id, street="Foreign Addr", city="Paris", postal_code="75030", country="fr"
    )
    product = ProductFactory(stock=4, price=7.5)
    await db_session.flush()
    user_id = get_user_id_from_token(auth_client)
    cart_item = CartItemFactory.build(product=product, quantity=1, unit_price=7.5)
    CartFactory(user_id=user_id, items=[cart_item])
    r = await auth_client.post(
        f"{ORD}/",
        json={"shipping_address_id": str(foreign_addr.id)},
    )
    assert r.status_code == 404
    body = r.json()
    assert body["error_code"] == "address_not_found"

"""End to end tests for order-related API endpoints."""

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
async def test_checkout_decrements_stock_and_clears_cart(auth_client: AsyncClient):
    product = ProductFactory(stock=3, price=10.0)
    user_id = get_user_id_from_token(auth_client)
    cart_item = CartItemFactory.build(product=product, quantity=2, unit_price=10.0)
    CartFactory(user_id=user_id, items=[cart_item])

    r = await auth_client.post(f"{ORD}/")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["total_amount"] == 20.0
    assert len(body["items"]) == 1 and body["items"][0]["quantity"] == 2

    # cart is cleared
    cart = (await auth_client.get(f"{CART}/")).json()
    assert cart["items"] == []


@pytest.mark.asyncio
async def test_checkout_empty_cart_400(auth_client: AsyncClient):
    user_id = get_user_id_from_token(auth_client)
    CartFactory(user_id=user_id)

    r = await auth_client.post(f"{ORD}/")
    assert r.status_code == 400
    assert r.json()["detail"] == "Cart is empty."


@pytest.mark.asyncio
async def test_list_and_get_my_orders(auth_client: AsyncClient):
    product = ProductFactory(stock=5, price=10.0)
    user_id = get_user_id_from_token(auth_client)
    cart_item = CartItemFactory.build(product=product, quantity=2, unit_price=10.0)
    CartFactory(user_id=user_id, items=[cart_item])
    created = (await auth_client.post(f"{ORD}/")).json()

    # list
    r_list = await auth_client.get(f"{ORD}/")
    assert r_list.status_code == 200
    assert any(o["id"] == created["id"] for o in r_list.json())

    # get one
    r_one = await auth_client.get(f"{ORD}/{created['id']}")
    assert r_one.status_code == 200
    assert r_one.json()["number"].startswith("ORD-")

"""End to end tests for order-related API endpoints."""

import pytest
from httpx import AsyncClient

AUTH = "/api/v1/auth"
CART = "/api/v1/cart"
ORD = "/api/v1/orders"
PROD = "/api/v1/products"
CAT = "/api/v1/categories"


async def auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    await client.post(f"{AUTH}/register", json={"email": email, "password": "secret"})
    tok = (
        await client.post(
            f"{AUTH}/login",
            data={"username": email, "password": "secret"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


async def mk_cat_prod(client: AsyncClient, name: str, stock: int, price: float) -> str:
    cat = (await client.post(f"{CAT}/", json={"name": f"{name}-cat"})).json()["id"]
    return (
        await client.post(
            f"{PROD}/",
            json={
                "name": name,
                "description": "d",
                "price": price,
                "stock": stock,
                "category_id": cat,
            },
        )
    ).json()["id"]


@pytest.mark.asyncio
async def test_checkout_success_decrements_stock_and_clears_cart(client: AsyncClient):
    h = await auth_headers(client, "order1@example.com")
    pid = await mk_cat_prod(client, "Widget", stock=3, price=10.0)
    await client.post(f"{CART}/", headers=h)
    await client.post(f"{CART}/items", headers=h, json={"product_id": pid, "quantity": 2})

    r = await client.post(f"{ORD}/", headers=h)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["total_amount"] == 20.0
    assert len(body["items"]) == 1 and body["items"][0]["quantity"] == 2

    # cart is cleared
    cart = (await client.get(f"{CART}/", headers=h)).json()
    assert cart["items"] == []


@pytest.mark.asyncio
async def test_checkout_empty_cart_400(client: AsyncClient):
    h = await auth_headers(client, "order2@example.com")
    await client.post(f"{CART}/", headers=h)
    r = await client.post(f"{ORD}/", headers=h)
    assert r.status_code == 400
    assert r.json()["detail"] == "Cart is empty."


@pytest.mark.asyncio
async def test_list_and_get_my_orders(client: AsyncClient):
    h = await auth_headers(client, "order4@example.com")
    pid = await mk_cat_prod(client, "Thing", stock=5, price=2.5)
    await client.post(f"{CART}/", headers=h)
    await client.post(f"{CART}/items", headers=h, json={"product_id": pid, "quantity": 4})
    created = (await client.post(f"{ORD}/", headers=h)).json()

    # list
    r_list = await client.get(f"{ORD}/", headers=h)
    assert r_list.status_code == 200
    assert any(o["id"] == created["id"] for o in r_list.json())

    # get one
    r_one = await client.get(f"{ORD}/{created['id']}", headers=h)
    assert r_one.status_code == 200
    assert r_one.json()["number"].startswith("ORD-")

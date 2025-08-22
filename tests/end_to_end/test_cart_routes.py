"""End to end tests for cart-related API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

AUTH_BASE = "/api/v1/auth"
CART_BASE = "/api/v1/cart"
PRODUCTS_BASE = "/api/v1/products"
CATEGORIES_BASE = "/api/v1/categories"


# ---------------- Helpers ----------------


async def register(client: AsyncClient, email: str, password: str = "secret"):
    return await client.post(f"{AUTH_BASE}/register", json={"email": email, "password": password})


async def login_token(client: AsyncClient, email: str, password: str = "secret") -> str:
    r = await client.post(
        f"{AUTH_BASE}/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    await register(client, email)
    token = await login_token(client, email)
    return {"Authorization": f"Bearer {token}"}


async def create_category(client: AsyncClient, name: str) -> str:
    r = await client.post(f"{CATEGORIES_BASE}/", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def create_product(
    client: AsyncClient,
    name: str,
    category_id: str,
    price: float = 10.0,
    stock: int = 5,
    description: str = "desc",
) -> str:
    payload = {
        "name": name,
        "description": description,
        "price": price,
        "stock": stock,
        "category_id": category_id,
    }
    r = await client.post(f"{PRODUCTS_BASE}/", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ---------------- Auth bad cases (sanity) ----------------


@pytest.mark.asyncio
async def test_cart_requires_auth(client: AsyncClient):
    # All /cart endpoints should reject when unauthenticated
    assert (await client.get(f"{CART_BASE}/")).status_code == 401
    assert (
        await client.post(f"{CART_BASE}/items", json={"product_id": str(uuid4()), "quantity": 1})
    ).status_code == 401
    assert (
        await client.put(f"{CART_BASE}/items/{uuid4()}", json={"quantity": 1})
    ).status_code == 401
    assert (await client.delete(f"{CART_BASE}/items/{uuid4()}")).status_code == 401
    assert (await client.delete(f"{CART_BASE}/")).status_code == 401


# ---------------- Get ----------------


@pytest.mark.asyncio
async def test_get_my_cart_idempotent(client: AsyncClient):
    headers = await auth_headers(client, "mycart@example.com")

    r_create1 = await client.get(f"{CART_BASE}/", headers=headers)
    assert r_create1.status_code == 200, r_create1.text
    cart1 = r_create1.json()
    assert "id" in cart1 and cart1["items"] == []


# ---------------- Add Items ----------------


@pytest.mark.asyncio
async def test_add_item_success_and_increment_existing_line(client: AsyncClient):
    headers = await auth_headers(client, "additem@example.com")
    # Setup product
    cat_id = await create_category(client, "Electronics")
    prod_id = await create_product(client, "Phone", cat_id, price=99.0, stock=10)

    # Add quantity 1
    r_add1 = await client.post(
        f"{CART_BASE}/items", headers=headers, json={"product_id": prod_id, "quantity": 1}
    )
    assert r_add1.status_code == 200, r_add1.text
    cart_after_1 = r_add1.json()
    line = next(it for it in cart_after_1["items"] if it["product_id"] == prod_id)
    assert line["quantity"] == 1 and line["unit_price"] == 99.0

    # Add quantity 2 (increments)
    r_add2 = await client.post(
        f"{CART_BASE}/items", headers=headers, json={"product_id": prod_id, "quantity": 2}
    )
    assert r_add2.status_code == 200, r_add2.text
    cart_after_2 = r_add2.json()
    line2 = next(it for it in cart_after_2["items"] if it["product_id"] == prod_id)
    assert line2["quantity"] == 3


@pytest.mark.asyncio
async def test_add_item_blocked_by_stock(client: AsyncClient):
    headers = await auth_headers(client, "stock@example.com")
    cat = await create_category(client, "StockCat")
    prod = await create_product(client, "Limited", cat, price=10.0, stock=2)

    # add 2 -> ok
    r1 = await client.post(
        f"{CART_BASE}/items", headers=headers, json={"product_id": prod, "quantity": 2}
    )
    assert r1.status_code == 200

    # add 1 more -> exceed stock (2+1 > 2)
    r2 = await client.post(
        f"{CART_BASE}/items", headers=headers, json={"product_id": prod, "quantity": 1}
    )
    assert r2.status_code == 409
    assert r2.json()["detail"] == "Insufficient stock."


@pytest.mark.asyncio
async def test_add_item_product_not_found(client: AsyncClient):
    headers = await auth_headers(client, "baditem@example.com")

    r = await client.post(
        f"{CART_BASE}/items",
        headers=headers,
        json={"product_id": str(uuid4()), "quantity": 1},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Product not found."


@pytest.mark.asyncio
async def test_add_item_validation_errors(client: AsyncClient):
    headers = await auth_headers(client, "badpayload@example.com")

    # Missing product_id
    r1 = await client.post(f"{CART_BASE}/items", headers=headers, json={"quantity": 1})
    assert r1.status_code == 422

    # quantity < 1
    r2 = await client.post(
        f"{CART_BASE}/items", headers=headers, json={"product_id": str(uuid4()), "quantity": 0}
    )
    assert r2.status_code == 422


# ---------------- Update Item ----------------


@pytest.mark.asyncio
async def test_update_item_quantity_and_remove_when_zero(client: AsyncClient):
    headers = await auth_headers(client, "upd@example.com")
    cat_id = await create_category(client, "Toys")
    prod_id = await create_product(client, "Car", cat_id)

    added = await client.post(
        f"{CART_BASE}/items", headers=headers, json={"product_id": prod_id, "quantity": 1}
    )
    item_id = next(it["id"] for it in added.json()["items"] if it["product_id"] == prod_id)

    # Update qty -> 5
    r_upd = await client.put(f"{CART_BASE}/items/{item_id}", headers=headers, json={"quantity": 5})
    assert r_upd.status_code == 200
    assert next(it for it in r_upd.json()["items"] if it["id"] == item_id)["quantity"] == 5

    # Set qty -> 0 (remove)
    r_zero = await client.put(f"{CART_BASE}/items/{item_id}", headers=headers, json={"quantity": 0})
    assert r_zero.status_code == 200
    assert not any(it["id"] == item_id for it in r_zero.json()["items"])


@pytest.mark.asyncio
async def test_update_item_not_found(client: AsyncClient):
    headers = await auth_headers(client, "upd404@example.com")

    r = await client.put(f"{CART_BASE}/items/{uuid4()}", headers=headers, json={"quantity": 3})
    assert r.status_code == 404
    assert r.json()["detail"] == "Item not found in cart."


@pytest.mark.asyncio
async def test_update_item_blocked_by_stock(client: AsyncClient):
    headers = await auth_headers(client, "stockupd@example.com")
    cat = await create_category(client, "StockUpd")
    prod = await create_product(client, "Cap", cat, price=5.0, stock=3)

    _ = await client.post(f"{CART_BASE}/", headers=headers)
    added = await client.post(
        f"{CART_BASE}/items", headers=headers, json={"product_id": prod, "quantity": 1}
    )
    item_id = next(it["id"] for it in added.json()["items"] if it["product_id"] == prod)

    # try set quantity to 4 (> stock 3)
    r_upd = await client.put(f"{CART_BASE}/items/{item_id}", headers=headers, json={"quantity": 4})
    assert r_upd.status_code == 409
    assert r_upd.json()["detail"] == "Insufficient stock."

    # set to 3 -> ok
    r_ok = await client.put(f"{CART_BASE}/items/{item_id}", headers=headers, json={"quantity": 3})
    assert r_ok.status_code == 200
    assert next(it for it in r_ok.json()["items"] if it["id"] == item_id)["quantity"] == 3


# ---------------- Remove Item ----------------


@pytest.mark.asyncio
async def test_remove_item_success_then_404(client: AsyncClient):
    headers = await auth_headers(client, "rm@example.com")
    cat_id = await create_category(client, "Books")
    prod_id = await create_product(client, "Novel", cat_id)

    added = await client.post(
        f"{CART_BASE}/items", headers=headers, json={"product_id": prod_id, "quantity": 2}
    )
    item_id = next(it["id"] for it in added.json()["items"] if it["product_id"] == prod_id)

    r_del = await client.delete(f"{CART_BASE}/items/{item_id}", headers=headers)
    assert r_del.status_code == 204

    r_del_again = await client.delete(f"{CART_BASE}/items/{item_id}", headers=headers)
    assert r_del_again.status_code == 404
    assert r_del_again.json()["detail"] == "Item not found in cart."


# ---------------- Clear Cart (good & idempotent) ----------------


@pytest.mark.asyncio
async def test_clear_my_cart(client: AsyncClient):
    headers = await auth_headers(client, "clear@example.com")

    r1 = await client.delete(f"{CART_BASE}/", headers=headers)
    assert r1.status_code == 204

    # Clearing again stays 204
    r2 = await client.delete(f"{CART_BASE}/", headers=headers)
    assert r2.status_code == 204


# ---------------- Multi-user isolation ----------------


@pytest.mark.asyncio
async def test_carts_are_isolated_per_user(client: AsyncClient):
    headers_a = await auth_headers(client, "alice@example.com")
    headers_b = await auth_headers(client, "bob@example.com")

    cat_id = await create_category(client, "Games")
    prod_a = await create_product(client, "Chess", cat_id)
    prod_b = await create_product(client, "Go", cat_id)

    # Alice adds Chess (1)
    _ = await client.post(f"{CART_BASE}/", headers=headers_a)
    await client.post(
        f"{CART_BASE}/items", headers=headers_a, json={"product_id": prod_a, "quantity": 1}
    )

    # Bob adds Go (2)
    _ = await client.post(f"{CART_BASE}/", headers=headers_b)
    await client.post(
        f"{CART_BASE}/items", headers=headers_b, json={"product_id": prod_b, "quantity": 2}
    )

    # Alice's cart contains only Chess
    r_a = await client.get(f"{CART_BASE}/", headers=headers_a)
    assert r_a.status_code == 200
    items_a = r_a.json()["items"]
    assert len(items_a) == 1 and items_a[0]["product_id"] == prod_a

    # Bob's cart contains only Go
    r_b = await client.get(f"{CART_BASE}/", headers=headers_b)
    assert r_b.status_code == 200
    items_b = r_b.json()["items"]
    assert len(items_b) == 1 and items_b[0]["product_id"] == prod_b

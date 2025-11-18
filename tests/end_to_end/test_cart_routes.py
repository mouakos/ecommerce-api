"""End to end tests for cart-related API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.factories import CategoryFactory, ProductFactory

BASE = "/api/v1/cart"

# ---------------- Auth bad cases (sanity) ----------------


@pytest.mark.asyncio
async def test_cart_requires_auth(client: AsyncClient):
    # All /cart endpoints should reject when unauthenticated
    assert (await client.get(f"{BASE}/")).status_code == 403
    assert (
        await client.post(f"{BASE}/items", json={"product_id": str(uuid4()), "quantity": 1})
    ).status_code == 403
    assert (await client.patch(f"{BASE}/items/{uuid4()}", json={"quantity": 1})).status_code == 403
    assert (await client.delete(f"{BASE}/items/{uuid4()}")).status_code == 403
    assert (await client.delete(f"{BASE}/")).status_code == 403


# ---------------- Get ----------------


@pytest.mark.asyncio
async def test_get_my_cart_idempotent(auth_client: AsyncClient):
    r_create1 = await auth_client.get(f"{BASE}/")
    assert r_create1.status_code == 200, r_create1.text
    cart1 = r_create1.json()
    assert "id" in cart1 and cart1["items"] == []


# ---------------- Add Items ----------------


@pytest.mark.asyncio
async def test_add_item_success_and_increment_existing_line(auth_client: AsyncClient, db_session):
    # Setup product
    product = ProductFactory(price=99.0, stock=10)
    await db_session.flush()

    # Add quantity 1
    r_add1 = await auth_client.post(
        f"{BASE}/items", json={"product_id": str(product.id), "quantity": 1}
    )
    assert r_add1.status_code == 200, r_add1.text
    cart_after_1 = r_add1.json()
    line = next(it for it in cart_after_1["items"] if it["product_id"] == str(product.id))
    assert line["quantity"] == 1 and line["unit_price"] == 99.0

    # Add quantity 2 (increments)
    r_add2 = await auth_client.post(
        f"{BASE}/items", json={"product_id": str(product.id), "quantity": 2}
    )
    assert r_add2.status_code == 200, r_add2.text
    cart_after_2 = r_add2.json()
    line2 = next(it for it in cart_after_2["items"] if it["product_id"] == str(product.id))
    assert line2["quantity"] == 3


@pytest.mark.asyncio
async def test_add_item_blocked_by_stock(auth_client: AsyncClient, db_session):
    product = ProductFactory(price=10.0, stock=2)
    await db_session.flush()

    # add 2 -> ok
    r1 = await auth_client.post(
        f"{BASE}/items", json={"product_id": str(product.id), "quantity": 2}
    )
    assert r1.status_code == 200

    # add 1 more -> exceed stock (2+1 > 2)
    r2 = await auth_client.post(
        f"{BASE}/items", json={"product_id": str(product.id), "quantity": 1}
    )
    assert r2.status_code == 400
    assert r2.json()["detail"] == "Insufficient stock."


@pytest.mark.asyncio
async def test_add_item_product_not_found(auth_client: AsyncClient):
    r = await auth_client.post(
        f"{BASE}/items",
        json={"product_id": str(uuid4()), "quantity": 1},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Product not found."


@pytest.mark.asyncio
async def test_add_item_validation_errors(auth_client: AsyncClient):
    # Missing product_id
    r1 = await auth_client.post(f"{BASE}/items", json={"quantity": 1})
    assert r1.status_code == 422

    # quantity < 1
    r2 = await auth_client.post(f"{BASE}/items", json={"product_id": str(uuid4()), "quantity": 0})
    assert r2.status_code == 422


# ---------------- Update Item ----------------
@pytest.mark.asyncio
async def test_update_item_quantity_and_remove_when_zero(auth_client: AsyncClient, db_session):
    product = ProductFactory()
    await db_session.flush()

    added = await auth_client.post(
        f"{BASE}/items", json={"product_id": str(product.id), "quantity": 1}
    )
    item_id = next(it["id"] for it in added.json()["items"] if it["product_id"] == str(product.id))

    # Update qty -> 5
    r_upd = await auth_client.patch(f"{BASE}/items/{item_id}", json={"quantity": 5})
    assert r_upd.status_code == 200
    assert next(it for it in r_upd.json()["items"] if it["id"] == item_id)["quantity"] == 5

    # Set qty -> 0 (remove)
    r_zero = await auth_client.patch(f"{BASE}/items/{item_id}", json={"quantity": 0})
    assert r_zero.status_code == 200
    assert not any(it["id"] == item_id for it in r_zero.json()["items"])


@pytest.mark.asyncio
async def test_update_item_not_found(auth_client: AsyncClient):
    r = await auth_client.patch(f"{BASE}/items/{uuid4()}", json={"quantity": 3})
    assert r.status_code == 404
    assert r.json()["detail"] == "Cart item not found."


@pytest.mark.asyncio
async def test_update_item_blocked_by_stock(auth_client: AsyncClient, db_session):
    product = ProductFactory(stock=3)
    await db_session.flush()

    _ = await auth_client.post(f"{BASE}/")
    added = await auth_client.post(
        f"{BASE}/items", json={"product_id": str(product.id), "quantity": 1}
    )
    item_id = next(it["id"] for it in added.json()["items"] if it["product_id"] == str(product.id))

    # try set quantity to 4 (> stock 3)
    r_upd = await auth_client.patch(f"{BASE}/items/{item_id}", json={"quantity": 4})
    assert r_upd.status_code == 400
    assert r_upd.json()["detail"] == "Insufficient stock."

    # set to 3 -> ok
    r_ok = await auth_client.patch(f"{BASE}/items/{item_id}", json={"quantity": 3})
    assert r_ok.status_code == 200
    assert next(it for it in r_ok.json()["items"] if it["id"] == item_id)["quantity"] == 3


# ---------------- Remove Item ----------------
@pytest.mark.asyncio
async def test_remove_item_success_then_404(auth_client: AsyncClient, db_session):
    product = ProductFactory()
    await db_session.flush()

    added = await auth_client.post(
        f"{BASE}/items", json={"product_id": str(product.id), "quantity": 2}
    )
    item_id = next(it["id"] for it in added.json()["items"] if it["product_id"] == str(product.id))

    r_del = await auth_client.delete(f"{BASE}/items/{item_id}")
    assert r_del.status_code == 204

    r_del_again = await auth_client.delete(f"{BASE}/items/{item_id}")
    assert r_del_again.status_code == 404
    assert r_del_again.json()["detail"] == "Cart item not found."


# ---------------- Clear Cart (good & idempotent) ----------------


@pytest.mark.asyncio
async def test_clear_my_cart(auth_client: AsyncClient):
    r1 = await auth_client.delete(f"{BASE}/")
    assert r1.status_code == 204

    # Clearing again stays 204
    r2 = await auth_client.delete(f"{BASE}/")
    assert r2.status_code == 204


# ---------------- Multi-user isolation ----------------


@pytest.mark.asyncio
async def test_carts_are_isolated_per_user(
    auth_client: AsyncClient, auth_admin_client: AsyncClient, db_session
):
    category = CategoryFactory()
    product_a = ProductFactory(name="Chess", category=category, stock=5)
    product_b = ProductFactory(name="Go", category=category, stock=5)
    await db_session.flush()

    # Alice adds Chess (1)
    await auth_client.post(f"{BASE}/items", json={"product_id": str(product_a.id), "quantity": 1})

    # Bob adds Go (2)
    await auth_admin_client.post(
        f"{BASE}/items", json={"product_id": str(product_b.id), "quantity": 2}
    )

    # Alice's cart contains only Chess
    r_a = await auth_client.get(f"{BASE}/")
    assert r_a.status_code == 200
    items_a = r_a.json()["items"]
    assert len(items_a) == 1 and items_a[0]["product_id"] == str(product_a.id)

    # Bob's cart contains only Go
    r_b = await auth_admin_client.get(f"{BASE}/")
    assert r_b.status_code == 200
    items_b = r_b.json()["items"]
    assert len(items_b) == 1 and items_b[0]["product_id"] == str(product_b.id)

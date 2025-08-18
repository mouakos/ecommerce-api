"""Test cases for product API routes (good and bad cases)."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

PRODUCTS_BASE = "/api/v1/products"
CATEGORIES_BASE = "/api/v1/categories"


# ------- Helpers / Fixtures -------


@pytest.fixture
async def category(client: AsyncClient):
    # Create a category to attach products to
    name = f"Cat-{uuid4().hex[:6]}"
    r = await client.post(f"{CATEGORIES_BASE}/", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()  # {"id": "...", "name": "..."}


@pytest.fixture
async def other_category(client: AsyncClient):
    name = f"Cat-{uuid4().hex[:6]}"
    r = await client.post(f"{CATEGORIES_BASE}/", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()


async def create_product(
    client: AsyncClient,
    *,
    name: str,
    category_id: str,
    price: float = 10.0,
    stock: int = 5,
    description: str | None = "desc",
):
    payload = {
        "name": name,
        "description": description,
        "price": price,
        "stock": stock,
        "category_id": category_id,
    }
    return await client.post(f"{PRODUCTS_BASE}/", json=payload)


# ------- Tests: CREATE -------


@pytest.mark.asyncio
async def test_create_product_success(client: AsyncClient, category):
    r = await create_product(client, name="Phone", category_id=category["id"])
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "Phone"
    assert body["category_id"] == category["id"]
    assert body["price"] == 10.0
    assert body["stock"] == 5
    assert "id" in body


@pytest.mark.asyncio
async def test_create_product_validation_errors(client: AsyncClient, category):
    # Missing required field (price)
    bad = {
        "name": "NoPrice",
        "stock": 3,
        "category_id": category["id"],
    }
    r = await client.post(f"{PRODUCTS_BASE}/", json=bad)
    assert r.status_code == 422  # Pydantic validation

    # Negative price
    r = await create_product(client, name="BadPrice", category_id=category["id"], price=-1.0)
    assert r.status_code == 422

    # Negative stock
    r = await create_product(client, name="BadStock", category_id=category["id"], stock=-3)
    assert r.status_code == 422

    # Too short name
    r = await create_product(client, name="A", category_id=category["id"])
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_product_duplicate_name_same_category_conflict(client: AsyncClient, category):
    r1 = await create_product(client, name="Duplicated", category_id=category["id"])
    assert r1.status_code == 201, r1.text

    r2 = await create_product(client, name="Duplicated", category_id=category["id"])
    assert r2.status_code == 409
    assert r2.json()["detail"] == "Product with this name already exists in the category."


@pytest.mark.asyncio
async def test_create_product_same_name_different_categories_success(
    client: AsyncClient, category, other_category
):
    r1 = await create_product(client, name="SharedName", category_id=category["id"])
    r2 = await create_product(client, name="SharedName", category_id=other_category["id"])
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text


# ------- Tests: LIST -------


@pytest.mark.asyncio
async def test_list_products_empty(client: AsyncClient):
    r = await client.get(f"{PRODUCTS_BASE}/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_list_products_after_creations(client: AsyncClient, category):
    await create_product(client, name="AAA", category_id=category["id"])
    await create_product(client, name="BBB", category_id=category["id"])
    r = await client.get(f"{PRODUCTS_BASE}/")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert "AAA" in names and "BBB" in names


# ------- Tests: GET -------


@pytest.mark.asyncio
async def test_get_product_success(client: AsyncClient, category):
    created = (await create_product(client, name="GetMe", category_id=category["id"])).json()
    r = await client.get(f"{PRODUCTS_BASE}/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "GetMe"


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient):
    r = await client.get(f"{PRODUCTS_BASE}/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Product not found."


# ------- Tests: UPDATE -------


@pytest.mark.asyncio
async def test_update_product_success(client: AsyncClient, category):
    created = (await create_product(client, name="Old", category_id=category["id"])).json()
    payload = {"name": "New", "price": 15.5}
    r = await client.put(f"{PRODUCTS_BASE}/{created['id']}", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "New"
    assert body["price"] == 15.5


@pytest.mark.asyncio
async def test_update_product_not_found(client: AsyncClient):
    r = await client.put(f"{PRODUCTS_BASE}/{uuid4()}", json={"name": "X"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Product not found."


@pytest.mark.asyncio
async def test_update_product_duplicate_name_same_category_conflict(client: AsyncClient, category):
    _ = (await create_product(client, name="ProdA", category_id=category["id"])).json()
    b = (await create_product(client, name="ProdB", category_id=category["id"])).json()

    # Try renaming B to A in same category -> violates (category_id, name) unique
    r = await client.put(f"{PRODUCTS_BASE}/{b['id']}", json={"name": "ProdA"})
    assert r.status_code == 409, r.text


# ------- Tests: DELETE -------


@pytest.mark.asyncio
async def test_delete_product_success_then_404_on_get(client: AsyncClient, category):
    created = (await create_product(client, name="TempDel", category_id=category["id"])).json()
    r_del = await client.delete(f"{PRODUCTS_BASE}/{created['id']}")
    assert r_del.status_code == 204

    r_get = await client.get(f"{PRODUCTS_BASE}/{created['id']}")
    assert r_get.status_code == 404
    assert r_get.json()["detail"] == "Product not found."


@pytest.mark.asyncio
async def test_delete_product_not_found(client: AsyncClient):
    r = await client.delete(f"{PRODUCTS_BASE}/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Product not found."

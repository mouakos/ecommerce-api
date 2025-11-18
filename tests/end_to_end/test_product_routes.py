"""End to end tests for product-related API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.factories import CategoryFactory, ProductFactory

BASE = "/api/v1/products"


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
    return await client.post(f"{BASE}/", json=payload)


# ------- Tests: CREATE -------


@pytest.mark.asyncio
async def test_create_product_success(auth_admin_client: AsyncClient, db_session):
    category = CategoryFactory()
    await db_session.flush()
    r = await create_product(auth_admin_client, name="Phone", category_id=str(category.id))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "Phone"
    assert body["category_id"] == str(category.id)
    assert body["price"] == 10.0
    assert body["stock"] == 5
    assert "id" in body


@pytest.mark.asyncio
async def test_create_product_validation_errors(auth_admin_client: AsyncClient, db_session):
    category = CategoryFactory()
    await db_session.flush()
    # Missing required field (price)
    bad = {
        "name": "NoPrice",
        "stock": 3,
        "category_id": str(category.id),
    }
    r = await auth_admin_client.post(f"{BASE}/", json=bad)
    assert r.status_code == 422  # Pydantic validation

    # Negative price
    r = await create_product(
        auth_admin_client, name="BadPrice", category_id=str(category.id), price=-1.0
    )
    assert r.status_code == 422

    # Negative stock
    r = await create_product(
        auth_admin_client, name="BadStock", category_id=str(category.id), stock=-3
    )
    assert r.status_code == 422

    # Too short name
    r = await create_product(auth_admin_client, name="A", category_id=str(category.id))
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_product_duplicate_name_same_category_conflict(
    auth_admin_client: AsyncClient, db_session
):
    category = CategoryFactory()
    await db_session.flush()
    r1 = await create_product(auth_admin_client, name="Duplicated", category_id=str(category.id))
    assert r1.status_code == 201, r1.text

    r2 = await create_product(auth_admin_client, name="Duplicated", category_id=str(category.id))
    assert r2.status_code == 409
    assert r2.json()["detail"] == "Product already exists."


@pytest.mark.asyncio
async def test_create_product_same_name_different_categories_success(
    auth_admin_client: AsyncClient, db_session
):
    category = CategoryFactory()
    other_category = CategoryFactory()
    await db_session.flush()
    r1 = await create_product(auth_admin_client, name="SharedName", category_id=str(category.id))
    r2 = await create_product(
        auth_admin_client, name="SharedName", category_id=str(other_category.id)
    )
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text


# ------- Tests: LIST -------


@pytest.mark.asyncio
async def test_list_products_empty(client: AsyncClient):
    r = await client.get(f"{BASE}/")
    assert r.status_code == 200
    assert isinstance(r.json()["items"], list)


@pytest.mark.asyncio
async def test_list_products_after_creations(client: AsyncClient, db_session):
    ProductFactory.create(name="AAA")
    ProductFactory.create(name="BBB")
    await db_session.flush()

    r = await client.get(f"{BASE}/")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()["items"]]
    assert "AAA" in names and "BBB" in names


@pytest.mark.asyncio
async def test_list_products_paged_and_filtered(client: AsyncClient, db_session):
    category = CategoryFactory()
    other_category = CategoryFactory()
    ProductFactory(name="Phone", price=99.0, stock=5, description="smart phone", category=category)
    ProductFactory(name="Laptop", price=899.0, stock=0, description="ultra-book", category=category)
    ProductFactory(name="Novel", price=15.0, stock=10, description="book", category=other_category)
    await db_session.flush()

    # Basic page
    r = await client.get(f"{BASE}/?limit=2&offset=0&sort=name")
    assert r.status_code == 200
    page = r.json()
    assert page["limit"] == 2 and page["offset"] == 0
    assert len(page["items"]) <= 2

    # Filter by category
    r_cat = await client.get(f"{BASE}/?category_id={category.id}")
    assert all(it["category_id"] == str(category.id) for it in r_cat.json()["items"])

    # Price range
    r_price = await client.get(f"{BASE}/?price_min=20&price_max=200")
    names = [it["name"] for it in r_price.json()["items"]]
    assert "Phone" in names and "Novel" not in names

    # In-stock only
    r_stock = await client.get(f"{BASE}/?in_stock=true")
    assert all(it["stock"] > 0 for it in r_stock.json()["items"])

    # q search (name/description, case-insensitive)
    r_q = await client.get(f"{BASE}/?q=BOOK")
    names_q = [it["name"] for it in r_q.json()["items"]]
    assert (
        "Novel" in names_q or "Laptop" in names_q
    )  # "book" in description of Novel, "ultra-book" in Laptop

    # Sort descending by price
    r_sort = await client.get(f"{BASE}/?sort=-price")
    items = r_sort.json()["items"]
    assert len(items) >= 2
    assert items[0]["price"] >= items[1]["price"]


# ------- Tests: GET -------


@pytest.mark.asyncio
async def test_get_product_success(client: AsyncClient, db_session):
    created = ProductFactory(name="GetMe")
    await db_session.flush()
    r = await client.get(f"{BASE}/{created.id}")
    assert r.status_code == 200
    assert r.json()["name"] == "GetMe"


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient):
    r = await client.get(f"{BASE}/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Product not found."


# ------- Tests: UPDATE -------


@pytest.mark.asyncio
async def test_update_product_success(auth_admin_client: AsyncClient, db_session):
    created = ProductFactory()
    await db_session.flush()
    payload = {"name": "New", "price": 15.5}
    r = await auth_admin_client.put(f"{BASE}/{created.id}", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "New"
    assert body["price"] == 15.5


@pytest.mark.asyncio
async def test_update_product_not_found(auth_admin_client: AsyncClient):
    r = await auth_admin_client.put(f"{BASE}/{uuid4()}", json={"name": "X"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Product not found."


@pytest.mark.asyncio
async def test_update_product_duplicate_name_same_category_conflict(
    auth_admin_client: AsyncClient, db_session
):
    category = CategoryFactory()
    ProductFactory.create(name="ProdA", category=category)
    b = ProductFactory.create(name="ProdB", category=category)
    await db_session.flush()

    # Try renaming B to A in same category -> violates (category_id, name) unique
    r = await auth_admin_client.put(f"{BASE}/{b.id}", json={"name": "ProdA"})
    assert r.status_code == 409
    assert r.json()["detail"] == "Product already exists."


# ------- Tests: DELETE -------


@pytest.mark.asyncio
async def test_delete_product_success_then_404_on_get(auth_admin_client: AsyncClient, db_session):
    created = ProductFactory.create(name="TempDel")
    await db_session.flush()
    r_del = await auth_admin_client.delete(f"{BASE}/{created.id}")
    assert r_del.status_code == 204

    r_get = await auth_admin_client.get(f"{BASE}/{created.id}")
    assert r_get.status_code == 404
    assert r_get.json()["detail"] == "Product not found."


@pytest.mark.asyncio
async def test_delete_product_not_found(auth_admin_client: AsyncClient):
    r = await auth_admin_client.delete(f"{BASE}/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Product not found."

"""Test cases for category routes."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

CATEGORIES_BASE = "/api/v1/categories"


# ---------- Helpers ----------


async def create_category(client: AsyncClient, *, name: str):
    return await client.post(f"{CATEGORIES_BASE}/", json={"name": name})


# ---------- CREATE ----------


@pytest.mark.asyncio
async def test_create_category_success(client: AsyncClient):
    r = await create_category(client, name="e-Books")
    assert r.status_code == 201, r.text
    body = r.json()
    assert "id" in body
    assert body["name"] == "e-Books"


@pytest.mark.asyncio
async def test_create_category_validation_errors(client: AsyncClient):
    # Missing name
    r = await client.post(f"{CATEGORIES_BASE}/", json={})
    assert r.status_code == 422

    # Too short name (if you have min_length=2 on the field)
    r = await create_category(client, name="A")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_category_duplicate_name_conflict(client: AsyncClient):
    # If you added a unique index on 'name', the second create should fail.
    r1 = await create_category(client, name="UniqueCat")
    r2 = await create_category(client, name="UniqueCat")
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 409, r2.text


# ---------- LIST ----------


@pytest.mark.asyncio
async def test_list_categories_empty(client: AsyncClient):
    r = await client.get(f"{CATEGORIES_BASE}/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_list_categories_after_creations(client: AsyncClient):
    await create_category(client, name=f"Cat-{uuid4().hex[:6]}")
    await create_category(client, name=f"Cat-{uuid4().hex[:6]}")
    r = await client.get(f"{CATEGORIES_BASE}/")
    assert r.status_code == 200
    assert len(r.json()) >= 2


# ---------- GET ----------


@pytest.mark.asyncio
async def test_get_category_success(client: AsyncClient):
    created = (await create_category(client, name="GetMe")).json()
    r = await client.get(f"{CATEGORIES_BASE}/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "GetMe"


@pytest.mark.asyncio
async def test_get_category_not_found(client: AsyncClient):
    r = await client.get(f"{CATEGORIES_BASE}/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Category not found."


# ---------- UPDATE ----------


@pytest.mark.asyncio
async def test_update_category_success(client: AsyncClient):
    created = (await create_category(client, name="OldName")).json()
    r = await client.put(
        f"{CATEGORIES_BASE}/{created['id']}",
        json={"name": "NewName"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "NewName"


@pytest.mark.asyncio
async def test_update_category_not_found(client: AsyncClient):
    r = await client.put(f"{CATEGORIES_BASE}/{uuid4()}", json={"name": "Whatever"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Category not found."


@pytest.mark.asyncio
async def test_update_category_duplicate_name_conflict(client: AsyncClient):
    _ = (await create_category(client, name="Electronics")).json()
    b = (await create_category(client, name="Decoration")).json()

    # Try renaming Decoration -> Electronics
    r = await client.put(f"{CATEGORIES_BASE}/{b['id']}", json={"name": "Electronics"})
    assert r.status_code == 409
    assert r.json()["detail"] == "Category with this name already exists."


# ---------- DELETE ----------


@pytest.mark.asyncio
async def test_delete_category_success_then_404_on_get(client: AsyncClient):
    created = (await create_category(client, name="ToDelete")).json()
    r_del = await client.delete(f"{CATEGORIES_BASE}/{created['id']}")
    assert r_del.status_code == 204

    r_get = await client.get(f"{CATEGORIES_BASE}/{created['id']}")
    assert r_get.status_code == 404
    assert r_get.json()["detail"] == "Category not found."


@pytest.mark.asyncio
async def test_delete_category_not_found(client: AsyncClient):
    r = await client.delete(f"{CATEGORIES_BASE}/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Category not found."

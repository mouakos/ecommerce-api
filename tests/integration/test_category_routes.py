"""Test cases for category routes."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

BASE = "/api/v1/categories"


@pytest.mark.asyncio
async def test_list_empty(client: AsyncClient):
    r = await client.get(f"{BASE}/")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_success(client: AsyncClient):
    r = await client.post(f"{BASE}/", json={"name": "Books"})
    assert r.status_code == 201
    data = r.json()
    assert "id" in data and data["name"] == "Books"


@pytest.mark.asyncio
async def test_get_by_id_success(client: AsyncClient):
    created = (await client.post(f"{BASE}/", json={"name": "Games"})).json()
    r = await client.get(f"{BASE}/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Games"


@pytest.mark.asyncio
async def test_get_by_id_not_found(client: AsyncClient):
    missing_id = str(uuid4())
    r = await client.get(f"{BASE}/{missing_id}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Category not found."


@pytest.mark.asyncio
async def test_update_success(client: AsyncClient):
    created = (await client.post(f"{BASE}/", json={"name": "Electronics"})).json()
    r = await client.put(f"{BASE}/{created['id']}", json={"name": "Audio"})
    assert r.status_code == 200
    assert r.json()["name"] == "Audio"


@pytest.mark.asyncio
async def test_update_not_found(client: AsyncClient):
    r = await client.put(f"{BASE}/{uuid4()}", json={"name": "Whatever"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Category not found."


@pytest.mark.asyncio
async def test_delete_success_then_404_on_get(client: AsyncClient):
    created = (await client.post(f"{BASE}/", json={"name": "Temp"})).json()
    r_del = await client.delete(f"{BASE}/{created['id']}")
    r_get = await client.get(f"{BASE}/{created['id']}")
    assert r_del.status_code == 204
    assert r_get.status_code == 404


@pytest.mark.asyncio
async def test_delete_not_found_is_still_204(client: AsyncClient):
    # Your handler silently returns 204 even if it didn't exist (idempotent delete)
    r = await client.delete(f"{BASE}/{uuid4()}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_create_validation_error_short_name(client: AsyncClient):
    r = await client.post(f"{BASE}/", json={"name": "A"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_duplicate_name_conflict(client: AsyncClient):
    r1 = await client.post(f"{BASE}/", json={"name": "Clothes"})
    r2 = await client.post(f"{BASE}/", json={"name": "Clothes"})
    assert r1.status_code == 201
    assert r2.status_code == 409

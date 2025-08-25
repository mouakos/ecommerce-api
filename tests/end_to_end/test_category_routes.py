"""End to end tests for category-related API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

BASE = "/api/v1/categories"


# ---------- Helpers ----------


async def create_category(client: AsyncClient, *, name: str):
    return await client.post(f"{BASE}/", json={"name": name})


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
    r = await client.post(f"{BASE}/", json={})
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
async def test_pagination_basic_shape_and_ordering(client: AsyncClient):
    # Seed predictable names so alphabetical order is known
    names = [f"Cat-{i:02d}" for i in range(15)]
    for n in names:
        await create_category(client, name=n)

    r1 = await client.get(f"{BASE}/?limit=5&offset=0")
    assert r1.status_code == 200
    p1 = r1.json()
    assert p1["limit"] == 5 and p1["offset"] == 0
    assert p1["total"] >= 15
    page1_names = [it["name"] for it in p1["items"]]
    # ordered by name ascending
    assert page1_names == sorted(page1_names)

    r2 = await client.get(f"{BASE}/?limit=5&offset=5")
    p2 = r2.json()
    page2_names = [it["name"] for it in p2["items"]]

    # No overlap between pages 1 and 2
    assert set(page1_names).isdisjoint(page2_names)


@pytest.mark.asyncio
async def test_last_partial_page_and_empty_page(client: AsyncClient):
    # 13 items total -> pages of 5: 5,5,3, then empty
    # (Re-seed only if your test DB resets per test; otherwise ensure at least 13 exist)
    for i in range(13):
        await create_category(client, name=f"P-{i:02d}")

    r_full = await client.get(f"{BASE}/?limit=5&offset=10")
    assert r_full.status_code == 200
    last = r_full.json()
    assert last["limit"] == 5 and last["offset"] == 10
    assert len(last["items"]) == 3  # partial last page

    # empty page beyond total
    r_empty = await client.get(f"{BASE}/?limit=5&offset={last['total']}")
    empty = r_empty.json()
    assert empty["items"] == []


@pytest.mark.asyncio
async def test_limit_and_offset_guards(client: AsyncClient):
    r = await client.get(f"{BASE}/?limit=999&offset=-50")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_pagination_with_search(client: AsyncClient):
    # Ensure both matching and non-matching names exist
    await create_category(client, name="Books")
    await create_category(client, name="Board Games")
    await create_category(client, name="Electronics")

    # Search "bo" -> Books, Board Games (case-insensitive)
    r = await client.get(f"{BASE}/?search=Bo&limit=10&offset=0")
    assert r.status_code == 200
    page = r.json()
    names = [it["name"] for it in page["items"]]
    assert all("bo" in n.lower() for n in names)
    # And total reflects filtered count (not global)
    assert page["total"] == len(names)


@pytest.mark.asyncio
@pytest.mark.parametrize("limit,offset", [(1, 0), (2, 2), (3, 3), (5, 5)])
async def test_no_gaps_no_dupes_across_pages(client: AsyncClient, limit, offset):
    # Create 10 predictable categories
    base = [f"S-{i:02d}" for i in range(10)]
    for n in base:
        await create_category(client, name=n)

    # Collect two adjacent slices and ensure union equals the combined slice
    r_a = await client.get(f"{BASE}/?limit={limit}&offset={offset}")
    r_b = await client.get(f"{BASE}/?limit={limit}&offset={offset + limit}")
    a = [x["name"] for x in r_a.json()["items"]]
    b = [x["name"] for x in r_b.json()["items"]]
    # No duplicates across adjacent pages
    assert set(a).isdisjoint(b)


@pytest.mark.asyncio
async def test_list_categories_empty(client: AsyncClient):
    r = await client.get(f"{BASE}/")
    assert r.status_code == 200
    assert isinstance(r.json()["items"], list)


@pytest.mark.asyncio
async def test_list_categories_after_creations(client: AsyncClient):
    await create_category(client, name=f"Cat-{uuid4().hex[:6]}")
    await create_category(client, name=f"Cat-{uuid4().hex[:6]}")
    r = await client.get(f"{BASE}/")
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 2


# ---------- GET ----------


@pytest.mark.asyncio
async def test_get_category_success(client: AsyncClient):
    created = (await create_category(client, name="GetMe")).json()
    r = await client.get(f"{BASE}/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "GetMe"


@pytest.mark.asyncio
async def test_get_category_not_found(client: AsyncClient):
    r = await client.get(f"{BASE}/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Category not found."


# ---------- UPDATE ----------


@pytest.mark.asyncio
async def test_update_category_success(client: AsyncClient):
    created = (await create_category(client, name="OldName")).json()
    r = await client.put(
        f"{BASE}/{created['id']}",
        json={"name": "NewName"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "NewName"


@pytest.mark.asyncio
async def test_update_category_not_found(client: AsyncClient):
    r = await client.put(f"{BASE}/{uuid4()}", json={"name": "Whatever"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Category not found."


@pytest.mark.asyncio
async def test_update_category_duplicate_name_conflict(client: AsyncClient):
    _ = (await create_category(client, name="Electronics")).json()
    b = (await create_category(client, name="Decoration")).json()

    # Try renaming Decoration -> Electronics
    r = await client.put(f"{BASE}/{b['id']}", json={"name": "Electronics"})
    assert r.status_code == 409
    assert r.json()["detail"] == "Category with this name already exists."


# ---------- DELETE ----------


@pytest.mark.asyncio
async def test_delete_category_success_then_404_on_get(client: AsyncClient):
    created = (await create_category(client, name="ToDelete")).json()
    r_del = await client.delete(f"{BASE}/{created['id']}")
    assert r_del.status_code == 204

    r_get = await client.get(f"{BASE}/{created['id']}")
    assert r_get.status_code == 404
    assert r_get.json()["detail"] == "Category not found."


@pytest.mark.asyncio
async def test_delete_category_not_found(client: AsyncClient):
    r = await client.delete(f"{BASE}/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Category not found."

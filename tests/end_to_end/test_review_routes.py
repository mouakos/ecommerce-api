"""End to end tests for review-related API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.factories import ProductFactory

PROD_BASE = "/api/v1/products"
REV_BASE = "/api/v1"


async def create_review(
    client: AsyncClient, product_id: str, rating: int = 5, comment: str | None = "Great"
):
    return await client.post(
        f"{REV_BASE}/products/{product_id}/reviews", json={"rating": rating, "comment": comment}
    )


# ---------- CREATE ----------


@pytest.mark.asyncio
async def test_create_review_success(auth_client: AsyncClient, db_session):
    product = ProductFactory()
    await db_session.flush()
    r = await create_review(auth_client, str(product.id), rating=4, comment="Nice")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["rating"] == 4 and body["comment"] == "Nice"
    assert body["product_id"] == str(product.id)


@pytest.mark.asyncio
async def test_create_review_duplicate_conflict(auth_client: AsyncClient, db_session):
    product = ProductFactory()
    await db_session.flush()
    first = await create_review(auth_client, str(product.id), 5, "First")
    assert first.status_code == 201
    dup = await create_review(auth_client, str(product.id), 3, "Second")
    assert dup.status_code == 409
    assert dup.json()["detail"] == "User has already reviewed this product."


@pytest.mark.asyncio
async def test_create_review_product_not_found(auth_client: AsyncClient):
    r = await create_review(auth_client, str(uuid4()), 5, "Ghost")
    assert r.status_code == 404
    assert r.json()["detail"] == "Product not found."


# ---------- LIST ----------


@pytest.mark.asyncio
async def test_list_reviews_visible_only_for_regular_user(
    auth_client: AsyncClient, auth_admin_client: AsyncClient, db_session
):
    product = ProductFactory()
    await db_session.flush()
    # user adds two reviews on same product? not allowed -> need different users, so admin adds one, user adds another
    r_user = await create_review(auth_client, str(product.id), 4, "User")
    r_admin = await create_review(auth_admin_client, str(product.id), 2, "Admin")
    assert r_user.status_code == 201 and r_admin.status_code == 201

    # Admin hides their own review
    admin_review_id = r_admin.json()["id"]
    r_hide = await auth_admin_client.patch(
        f"{REV_BASE}/reviews/{admin_review_id}/visibility", json={"is_visible": False}
    )
    assert r_hide.status_code == 200 and r_hide.json()["is_visible"] is False

    # Regular user listing should only see visible reviews (just theirs)
    r_list_user = await auth_client.get(f"{REV_BASE}/products/{product.id}/reviews")
    assert r_list_user.status_code == 200
    items_user = r_list_user.json()["items"]
    assert len(items_user) == 1 and items_user[0]["comment"] == "User"

    # Admin listing sees both (hidden included)
    r_list_admin = await auth_admin_client.get(f"{REV_BASE}/products/{product.id}/reviews")
    assert r_list_admin.status_code == 200
    items_admin = r_list_admin.json()["items"]
    assert len(items_admin) == 2


@pytest.mark.asyncio
async def test_list_reviews_ordering(
    auth_client: AsyncClient, auth_client1: AsyncClient, db_session
):
    """Create two reviews with different ratings and verify ordering asc/desc by rating."""
    product = ProductFactory()
    await db_session.flush()

    r_a = await create_review(auth_client, str(product.id), rating=5, comment="High")
    r_b = await create_review(auth_client1, str(product.id), rating=2, comment="Low")
    assert r_a.status_code == 201 and r_b.status_code == 201

    # Ascending order -> ratings should be [2, 5]
    r_asc = await auth_client.get(
        f"{REV_BASE}/products/{product.id}/reviews?order_by=rating&order_dir=asc&limit=10&offset=0"
    )
    assert r_asc.status_code == 200, r_asc.text
    ratings_asc = [it["rating"] for it in r_asc.json()["items"]]
    assert ratings_asc == sorted(ratings_asc)

    # Descending order -> ratings should be [5, 2]
    r_desc = await auth_client.get(
        f"{REV_BASE}/products/{product.id}/reviews?order_by=rating&order_dir=desc&limit=10&offset=0"
    )
    assert r_desc.status_code == 200, r_desc.text
    ratings_desc = [it["rating"] for it in r_desc.json()["items"]]
    assert ratings_desc == sorted(ratings_desc, reverse=True)


# ---------- GET ----------


@pytest.mark.asyncio
async def test_get_review_respects_visibility(
    auth_client: AsyncClient, auth_admin_client: AsyncClient, db_session
):
    product = ProductFactory()
    await db_session.flush()
    user_rev = await create_review(auth_client, str(product.id), 5, "Visible")
    assert user_rev.status_code == 201
    # Admin creates review and hides it
    admin_rev = await create_review(auth_admin_client, str(product.id), 3, "Hidden")
    admin_rev_id = admin_rev.json()["id"]
    await auth_admin_client.patch(
        f"{REV_BASE}/reviews/{admin_rev_id}/visibility", json={"is_visible": False}
    )

    # Regular user cannot fetch hidden admin review
    r_hidden = await auth_client.get(f"{REV_BASE}/reviews/{admin_rev_id}")
    assert r_hidden.status_code == 404
    assert r_hidden.json()["detail"] == "Review not found."

    # Admin can fetch hidden review
    r_admin_fetch = await auth_admin_client.get(f"{REV_BASE}/reviews/{admin_rev_id}")
    assert r_admin_fetch.status_code == 200
    assert r_admin_fetch.json()["comment"] == "Hidden"


# ---------- UPDATE ----------


@pytest.mark.asyncio
async def test_update_review_author_success(auth_client: AsyncClient, db_session):
    product = ProductFactory()
    await db_session.flush()
    created = await create_review(auth_client, str(product.id), 4, "Orig")
    review_id = created.json()["id"]
    r_upd = await auth_client.patch(
        f"{REV_BASE}/reviews/{review_id}", json={"comment": "Edited", "rating": 5}
    )
    assert r_upd.status_code == 200
    assert r_upd.json()["comment"] == "Edited" and r_upd.json()["rating"] == 5


@pytest.mark.asyncio
async def test_update_review_unauthorized_other_user(
    auth_client: AsyncClient, auth_client1: AsyncClient, db_session
):
    product = ProductFactory()
    await db_session.flush()
    created = await create_review(auth_client, str(product.id), 4, "Mine")
    review_id = created.json()["id"]
    r_other = await auth_client1.patch(f"{REV_BASE}/reviews/{review_id}", json={"rating": 2})
    assert r_other.status_code == 403
    assert r_other.json()["detail"] == "You do not have enough permissions to perform this action."


# ---------- DELETE ----------


@pytest.mark.asyncio
async def test_delete_review_author_success(auth_client: AsyncClient, db_session):
    product = ProductFactory()
    await db_session.flush()
    created = await create_review(auth_client, str(product.id), 5, "Temp")
    review_id = created.json()["id"]
    r_del = await auth_client.delete(f"{REV_BASE}/reviews/{review_id}")
    assert r_del.status_code == 204
    r_get = await auth_client.get(f"{REV_BASE}/reviews/{review_id}")
    assert r_get.status_code == 404
    assert r_get.json()["detail"] == "Review not found."


# ---------- AVERAGE SUMMARY ENDPOINT ----------


@pytest.mark.asyncio
async def test_average_summary_endpoint(
    auth_client: AsyncClient, auth_client1: AsyncClient, db_session
):
    product = ProductFactory()
    await db_session.flush()
    # Two different users add reviews
    r1 = await create_review(auth_client, str(product.id), 5, "Great")
    r2 = await create_review(auth_client1, str(product.id), 3, "Ok")
    assert r1.status_code == 201 and r2.status_code == 201
    # Fetch summary
    r_summary = await auth_client.get(f"{PROD_BASE}/{product.id}/reviews/summary")
    assert r_summary.status_code == 200
    summary = r_summary.json()
    assert summary["review_count"] == 2
    # Average should be (5+3)/2 = 4.0
    assert summary["average_rating"] == pytest.approx(4.0)

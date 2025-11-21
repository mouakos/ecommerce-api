"""Integration tests for address routes."""

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User

BASE = "/api/v1/addresses"


@pytest.mark.asyncio
async def test_create_address(auth_client: AsyncClient):
    """Create a single address with new line1/line2 fields."""
    payload = {
        "line1": "123 Main St",
        "city": "Paris",
        "state": "FR-IDF",
        "postal_code": "75001",
        "country": "fr",
    }
    r = await auth_client.post(BASE + "/", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["line1"] == "123 Main St"
    assert body["city"] == "Paris"
    assert body["state"] == "FR-IDF"


@pytest.mark.asyncio
async def test_list_addresses(auth_client: AsyncClient):
    """Create two addresses and list them (no defaults)."""
    for i in range(2):
        r = await auth_client.post(
            BASE + "/",
            json={
                "line1": f"{i} First Ave",
                "city": "Paris",
                "state": "FR-IDF",
                "postal_code": f"7500{i}",
                "country": "fr",
            },
        )
        assert r.status_code == 201
    r_list = await auth_client.get(BASE + "/")
    items = r_list.json()["items"]
    assert len(items) >= 2


@pytest.mark.asyncio
async def test_address_ownership_enforced(
    auth_client: AsyncClient, client: AsyncClient, db_session: AsyncSession
):
    # Create second user
    other = User(
        email="otheruser@example.com",
        hashed_password=get_password_hash("pass12345"),
        is_verified=True,
    )
    db_session.add(other)
    await db_session.flush()
    # Register & verify second user to obtain token
    from app.core.security import create_url_safe_token

    t = create_url_safe_token("otheruser@example.com")
    r_verify = await client.get(f"/api/v1/auth/verify/{t}")
    assert r_verify.status_code == 200
    r_login = await client.post(
        "/api/v1/auth/login", json={"email": "otheruser@example.com", "password": "pass12345"}
    )
    assert r_login.status_code == 200
    other_access = r_login.json()["access_token"]

    # user in auth_client creates address
    r_create = await auth_client.post(
        BASE + "/",
        json={
            "line1": "9 Secret St",
            "city": "Lyon",
            "state": "FR-ARA",
            "postal_code": "69000",
            "country": "fr",
        },
    )
    addr_id = r_create.json()["id"]

    # Other user attempts to access address -> 404
    r_get = await client.get(
        BASE + f"/{addr_id}", headers={"Authorization": f"Bearer {other_access}"}
    )
    assert r_get.status_code == 404
    assert r_get.json()["error_code"] == "address_not_found"

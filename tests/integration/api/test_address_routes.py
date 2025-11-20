"""Integration tests for address routes."""

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User

BASE = "/api/v1/addresses"


@pytest.mark.asyncio
async def test_create_first_address_sets_defaults(auth_client: AsyncClient):
    # current user is from auth_client fixture (already verified). Create first address.
    payload = {
        "street": "123 Main St",
        "city": "Paris",
        "postal_code": "75001",
        "country": "fr",
    }
    r = await auth_client.post(BASE + "/", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["is_default_shipping"] is True
    assert body["is_default_billing"] is True


@pytest.mark.asyncio
async def test_create_second_address_switch_default_shipping(auth_client: AsyncClient):
    # First address
    r1 = await auth_client.post(
        BASE + "/",
        json={"street": "1 First Ave", "city": "Paris", "postal_code": "75001", "country": "fr"},
    )
    assert r1.status_code == 201
    # Second address with explicit flag
    r2 = await auth_client.post(
        BASE + "/",
        json={
            "street": "2 Second Ave",
            "city": "Paris",
            "postal_code": "75002",
            "country": "fr",
            "set_default_shipping": True,
        },
    )
    assert r2.status_code == 201
    a2 = r2.json()
    assert a2["is_default_shipping"] is True
    # list and ensure only second is default shipping
    r_list = await auth_client.get(BASE + "/")
    items = r_list.json()["items"]
    defaults = [i for i in items if i["is_default_shipping"]]
    assert len(defaults) == 1 and defaults[0]["id"] == a2["id"]


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
        json={"street": "9 Secret St", "city": "Lyon", "postal_code": "69000", "country": "fr"},
    )
    addr_id = r_create.json()["id"]

    # Other user attempts to access address -> 404
    r_get = await client.get(
        BASE + f"/{addr_id}", headers={"Authorization": f"Bearer {other_access}"}
    )
    assert r_get.status_code == 404
    assert r_get.json()["error_code"] == "address_not_found"

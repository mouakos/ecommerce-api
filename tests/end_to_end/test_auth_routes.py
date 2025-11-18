"""End to end tests for authentication-related API endpoints."""

import pytest
from httpx import AsyncClient

BASE = "/api/v1/auth"


# ---------------- Helpers ----------------


async def register(client: AsyncClient, email: str, password: str):
    return await client.post(f"{BASE}/register", json={"email": email, "password": password})


async def login_json(client: AsyncClient, email: str, password: str):
    """Login using JSON body matching UserLogin schema."""
    return await client.post(
        f"{BASE}/login",
        json={"email": email, "password": password},
    )


async def token_for(client: AsyncClient, email: str, password: str) -> str:
    r = await login_json(client, email, password)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ---------------- Register ----------------


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    r1 = await register(client, "a@example.com", "secret")
    assert r1.status_code == 201, r1.text
    body = r1.json()
    assert "id" in body and body["email"] == "a@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    _ = await register(client, "a@example.com", "secret")
    r2 = await register(client, "a@example.com", "secret")
    assert r2.status_code == 409
    assert r2.json()["detail"] == "Email already registered."


@pytest.mark.asyncio
async def test_register_validation_error(client: AsyncClient):
    # Missing password
    r = await client.post(f"{BASE}/register", json={"email": "b@example.com"})
    assert r.status_code == 422

    # Missing email
    r = await client.post(f"{BASE}/register", json={"password": "secret"})
    assert r.status_code == 422

    # Short password
    r = await client.post(f"{BASE}/register", json={"email": "c@example.com", "password": "short"})
    assert r.status_code == 422


# ---------------- Login ----------------


@pytest.mark.asyncio
async def test_login_success_and_me(client: AsyncClient):
    await register(client, "c@example.com", "secret")
    token_resp = await login_json(client, "c@example.com", "secret")
    assert token_resp.status_code == 200, token_resp.text
    token = token_resp.json()["access_token"]

    r_me = await client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {token}"})
    assert r_me.status_code == 200
    me = r_me.json()
    assert me["email"] == "c@example.com"
    assert "id" in me


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await register(client, "d@example.com", "secret")
    r = await login_json(client, "d@example.com", "badpassword")
    assert r.status_code == 400
    assert r.json()["detail"] in ("Invalid email or password.",)


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient):
    r = await login_json(client, "nope@example.com", "whatever")
    assert r.status_code == 400
    assert r.json()["detail"] in ("Invalid email or password.",)


# ---------------- Me (protected) ----------------


@pytest.mark.asyncio
async def test_me_unauthorized_no_token(client: AsyncClient):
    r = await client.get(f"{BASE}/me")
    # HTTPBearer returns 403 when Authorization header is missing
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_me_with_invalid_token(client: AsyncClient):
    r = await client.get(f"{BASE}/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401
    # New error message per TokenBearer implementation
    assert r.json()["detail"] == "Invalid token."


@pytest.mark.asyncio
async def test_me_with_tampered_token(client: AsyncClient):
    await register(client, "e@example.com", "secret")
    token = await token_for(client, "e@example.com", "secret")
    # Tamper the token slightly
    bad = token[:-1] + ("a" if token[-1] != "a" else "b")
    r = await client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid token."


@pytest.mark.asyncio
async def test_logout_revokes_token(client: AsyncClient):
    await register(client, "logout@example.com", "secret")
    login_resp = await login_json(client, "logout@example.com", "secret")
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Logout
    r_logout = await client.post(f"{BASE}/logout", headers={"Authorization": f"Bearer {token}"})
    assert r_logout.status_code == 200

    # Attempt to reuse token
    r_me = await client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {token}"})
    assert r_me.status_code == 401
    assert r_me.json()["detail"] == "Token has been revoked."

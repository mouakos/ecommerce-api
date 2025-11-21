"""End to end tests for authentication-related API endpoints.

Updated to reflect email verification requirement: users must verify before
successful login. Tests now perform verification where needed and loosen
registration assertions to match new response payload.
"""

import pytest
from httpx import AsyncClient

from app.core.security import create_url_safe_token

BASE = "/api/v1/auth"


# ---------------- Helpers ----------------


async def register(client: AsyncClient, email: str, password: str):
    return await client.post(f"{BASE}/register", json={"email": email, "password": password})


async def verify(client: AsyncClient, email: str):
    token = create_url_safe_token(email)
    # Verification endpoint uses GET semantics
    return await client.get(f"{BASE}/verify/{token}")


async def login_json(client: AsyncClient, email: str, password: str):
    """Login using JSON body matching UserLogin schema."""
    return await client.post(
        f"{BASE}/login",
        json={"email": email, "password": password},
    )


async def token_for(client: AsyncClient, email: str, password: str) -> str:
    # Ensure verified prior to login
    await verify(client, email)
    r = await login_json(client, email, password)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ---------------- Register ----------------


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    r1 = await register(client, "a@example.com", "secret")
    assert r1.status_code == 201, r1.text
    body = r1.json()
    assert "message" in body and "verify" in body["message"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    _ = await register(client, "a@example.com", "secret")
    r2 = await register(client, "a@example.com", "secret")
    assert r2.status_code == 409
    assert r2.json()["detail"] == "User with this email already exists."


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
async def test_login_wrong_password(client: AsyncClient):
    await register(client, "d@example.com", "secret")
    r = await login_json(client, "d@example.com", "bad-password")
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid Email or Password."


@pytest.mark.asyncio
async def test_login_unverified_user_gets_account_not_verified(client: AsyncClient):
    await register(client, "unverified@example.com", "secret")
    r = await login_json(client, "unverified@example.com", "secret")
    assert r.status_code == 403
    body = r.json()
    assert body["detail"] == "User account is not verified."
    assert body["error_code"] == "account_not_verified"
    assert "verify" in body["solution"].lower()


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient):
    r = await login_json(client, "nope@example.com", "whatever")
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid Email or Password."


# ---------------- Token Type Requirements ----------------


@pytest.mark.asyncio
async def test_refresh_token_endpoint_requires_refresh_token(client: AsyncClient):
    """Using an access token on /refresh-token should raise RefreshTokenRequiredError (400)."""
    await register(client, "refresh-mismatch@example.com", "secret")
    await verify(client, "refresh-mismatch@example.com")
    login_resp = await login_json(client, "refresh-mismatch@example.com", "secret")
    assert login_resp.status_code == 200
    access = login_resp.json()["access_token"]
    # Call refresh-token with ACCESS token (wrong type)
    r = await client.get(f"{BASE}/refresh-token", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 400
    body = r.json()
    assert body["detail"] == "Please provide a valid refresh token."
    assert body["error_code"] == "refresh_token_required"


@pytest.mark.asyncio
async def test_logout_requires_access_token(client: AsyncClient):
    """Using a refresh token on /logout should raise AccessTokenRequiredError (400)."""
    await register(client, "access-mismatch@example.com", "secret")
    await verify(client, "access-mismatch@example.com")
    login_resp = await login_json(client, "access-mismatch@example.com", "secret")
    assert login_resp.status_code == 200
    refresh = login_resp.json()["refresh_token"]
    # Call logout with REFRESH token (wrong type)
    r = await client.post(f"{BASE}/logout", headers={"Authorization": f"Bearer {refresh}"})
    assert r.status_code == 400
    body = r.json()
    assert body["detail"] == "Please provide a valid access token."
    assert body["error_code"] == "access_token_required"

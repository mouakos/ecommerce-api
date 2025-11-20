"""Integration tests for user management routes."""

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.enums import UserRole
from app.core.security import get_password_hash
from app.models.user import User

BASE = "/api/v1/users"


@pytest.mark.asyncio
async def test_list_users_admin(auth_admin_client: AsyncClient, db_session: AsyncSession):
    # create some users
    for i in range(3):
        u = User(
            email=f"user{i}@example.com",
            hashed_password=get_password_hash("pass123"),
            is_verified=True,
        )
        db_session.add(u)
    await db_session.flush()

    r = await auth_admin_client.get(BASE + "/?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body and "items" in body
    assert body["total"] >= 3
    assert all("email" in itm for itm in body["items"])


@pytest.mark.asyncio
async def test_login_success_and_me(client: AsyncClient):
    """Register, verify, login, and fetch /users/me."""
    # Reuse auth flow here to ensure /users/me returns correct shape
    r_reg = await client.post(
        "/api/v1/auth/register", json={"email": "c@example.com", "password": "secret"}
    )
    assert r_reg.status_code == 201
    # verify
    from app.core.security import create_url_safe_token

    token = create_url_safe_token("c@example.com")
    r_verify = await client.get(f"/api/v1/auth/verify/{token}")
    assert r_verify.status_code == 200
    # login
    r_login = await client.post(
        "/api/v1/auth/login", json={"email": "c@example.com", "password": "secret"}
    )
    assert r_login.status_code == 200
    access = r_login.json()["access_token"]
    r_me = await client.get(BASE + "/me", headers={"Authorization": f"Bearer {access}"})
    assert r_me.status_code == 200, r_me.text
    me = r_me.json()
    assert me["email"] == "c@example.com"
    assert "id" in me


# ---------------- /users/me token edge cases ----------------


@pytest.mark.asyncio
async def test_me_unauthorized_no_token(client: AsyncClient):
    r = await client.get(BASE + "/me")
    # HTTPBearer returns 403 when Authorization header is missing
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_me_with_invalid_token(client: AsyncClient):
    r = await client.get(BASE + "/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token is invalid or expired."


@pytest.mark.asyncio
async def test_me_with_tampered_token(client: AsyncClient):
    # Register & verify
    r_reg = await client.post(
        "/api/v1/auth/register", json={"email": "e@example.com", "password": "secret"}
    )
    assert r_reg.status_code == 201
    from app.core.security import create_url_safe_token

    verify_token = create_url_safe_token("e@example.com")
    r_ver = await client.get(f"/api/v1/auth/verify/{verify_token}")
    assert r_ver.status_code == 200
    # Login
    r_login = await client.post(
        "/api/v1/auth/login", json={"email": "e@example.com", "password": "secret"}
    )
    assert r_login.status_code == 200
    access = r_login.json()["access_token"]
    # Tamper signature
    parts = access.split(".")
    parts[-1] = "xxxxinvalidsignature"
    bad = ".".join(parts)
    r = await client.get(BASE + "/me", headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token is invalid or expired."


@pytest.mark.asyncio
async def test_logout_revokes_token(client: AsyncClient):
    r_reg = await client.post(
        "/api/v1/auth/register", json={"email": "logout@example.com", "password": "secret"}
    )
    assert r_reg.status_code == 201
    from app.core.security import create_url_safe_token

    verify_token = create_url_safe_token("logout@example.com")
    r_ver = await client.get(f"/api/v1/auth/verify/{verify_token}")
    assert r_ver.status_code == 200
    r_login = await client.post(
        "/api/v1/auth/login", json={"email": "logout@example.com", "password": "secret"}
    )
    assert r_login.status_code == 200
    access = r_login.json()["access_token"]
    r_logout = await client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {access}"}
    )
    assert r_logout.status_code == 200
    r_me = await client.get(BASE + "/me", headers={"Authorization": f"Bearer {access}"})
    assert r_me.status_code == 401
    assert r_me.json()["detail"] == "Token is invalid or has been revoked."


@pytest.mark.asyncio
async def test_list_users_non_admin_forbidden(auth_client: AsyncClient):
    r = await auth_client.get(BASE + "/")
    assert r.status_code == 403
    body = r.json()
    assert body["error_code"] == "insufficient_permissions"


@pytest.mark.asyncio
async def test_update_me_profile(auth_client: AsyncClient):
    r = await auth_client.patch(BASE + "/me", json={"first_name": "Alice"})
    assert r.status_code == 200
    assert r.json()["first_name"] == "Alice"


@pytest.mark.asyncio
async def test_admin_activate_deactivate_user(
    auth_admin_client: AsyncClient, db_session: AsyncSession
):
    u = User(
        email="toggle@example.com",
        hashed_password=get_password_hash("pass1234"),
        is_verified=True,
    )
    db_session.add(u)
    await db_session.flush()
    user_id = str(u.id)

    r_deact = await auth_admin_client.post(f"{BASE}/{user_id}/deactivate")
    assert r_deact.status_code == 200
    await db_session.refresh(u)
    assert u.is_active is False

    r_act = await auth_admin_client.post(f"{BASE}/{user_id}/activate")
    assert r_act.status_code == 200
    await db_session.refresh(u)
    assert u.is_active is True


@pytest.mark.asyncio
async def test_admin_set_role(auth_admin_client: AsyncClient, db_session: AsyncSession):
    u = User(
        email="rolechange@example.com",
        hashed_password=get_password_hash("pass5678"),
        is_verified=True,
    )
    db_session.add(u)
    await db_session.flush()
    user_id = str(u.id)

    r = await auth_admin_client.post(f"{BASE}/{user_id}/role", json={"role": "admin"})
    assert r.status_code == 200
    await db_session.refresh(u)
    assert u.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_admin_delete_user(auth_admin_client: AsyncClient, db_session: AsyncSession):
    u = User(
        email="todelete@example.com",
        hashed_password=get_password_hash("passDel12"),
        is_verified=True,
    )
    db_session.add(u)
    await db_session.flush()
    user_id = str(u.id)

    r_del = await auth_admin_client.delete(f"{BASE}/{user_id}")
    assert r_del.status_code == 204
    # Attempt to fetch again should 404 via service (simulate via direct route call requires admin)
    r_get = await auth_admin_client.get(f"{BASE}/{user_id}")
    assert r_get.status_code == 404


@pytest.mark.asyncio
async def test_admin_delete_user_not_found(auth_admin_client: AsyncClient):
    import uuid

    fake_id = str(uuid.uuid4())
    r_del = await auth_admin_client.delete(f"{BASE}/{fake_id}")
    assert r_del.status_code == 404
    body = r_del.json()
    assert body["error_code"] == "user_not_found"


@pytest.mark.asyncio
async def test_delete_user_forbidden_non_admin(auth_client: AsyncClient, db_session: AsyncSession):
    # create another user to attempt deletion
    other = User(
        email="other@example.com",
        hashed_password=get_password_hash("OtherPass9"),
        is_verified=True,
    )
    db_session.add(other)
    await db_session.flush()
    other_id = str(other.id)
    r_del = await auth_client.delete(f"{BASE}/{other_id}")
    assert r_del.status_code == 403
    body = r_del.json()
    assert body["error_code"] == "insufficient_permissions"


@pytest.mark.asyncio
async def test_admin_list_user_addresses(auth_admin_client: AsyncClient, auth_client: AsyncClient):
    # create some addresses under normal user
    for i in range(2):
        r = await auth_client.post(
            "/api/v1/addresses/",
            json={
                "street": f"{i} AdminView Rd",
                "city": "Paris",
                "postal_code": f"7500{i}",
                "country": "fr",
            },
        )
        assert r.status_code == 201

    r_me = await auth_client.get("/api/v1/users/me")
    user_id = r_me.json()["id"]
    r_admin_list = await auth_admin_client.get(f"/api/v1/users/{user_id}/addresses")
    assert r_admin_list.status_code == 200
    body = r_admin_list.json()
    assert body["total"] >= 2
    assert all("street" in itm for itm in body["items"])

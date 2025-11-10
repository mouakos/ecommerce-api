# mypy: disable-error-code=return-value

"""API routes for user authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, oauth2_scheme
from app.core.config import settings
from app.core.enums import TokenType
from app.core.errors import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token_type,
)
from app.db.redis import add_token_to_blocklist, is_token_in_blocklist
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
REFRESH_COOKIE_NAME = "refresh_token"


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: Annotated[AsyncSession, Depends(get_session)]) -> UserRead:
    """Register a new user."""
    return await AuthService.create_user(db, data)


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Token:
    """Authenticate a user and return a JWT token."""
    user = await AuthService.authenticate_user(db, form.username, form.password)
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600,  # convert days to seconds,
    )

    return Token(access_token=access_token)


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    request: Request,
) -> Token:
    """Refresh the access token using a valid refresh token."""
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise UnauthorizedError("Refresh token missing.")

    payload = verify_token_type(refresh_token, expected_type=TokenType.REFRESH)
    if not payload:
        raise UnauthorizedError("Invalid or expired refresh token.")

    if await is_token_in_blocklist(payload["jti"]):
        raise UnauthorizedError("Token has been revoked.")

    access_token = create_access_token(subject=payload["sub"])
    return Token(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request, response: Response, access_token: str = Depends(oauth2_scheme)
) -> None:
    """Logout the current user by revoking the refresh token."""
    # Get the refresh token from the request cookies
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise UnauthorizedError("Refresh token missing.")

    # Revoke both tokens
    await add_token_to_blocklist(refresh_token["jti"])
    await add_token_to_blocklist(access_token["jti"])
    response.delete_cookie(REFRESH_COOKIE_NAME)


@router.get("/me", response_model=UserRead)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    """Get the current authenticated user."""
    return current_user

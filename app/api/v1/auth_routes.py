# mypy: disable-error-code=return-value

"""API routes for user authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.enums import TokenType
from app.core.errors import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token_type,
)
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


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
        key="refresh_token",
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
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise UnauthorizedError("Refresh token missing.")

    user_id = verify_token_type(refresh_token, expected_type=TokenType.REFRESH)
    if not user_id:
        raise UnauthorizedError("Invalid refresh token")

    access_token = create_access_token(subject=user_id)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    """Get the current authenticated user."""
    return current_user

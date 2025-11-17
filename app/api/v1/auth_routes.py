# mypy: disable-error-code=return-value

"""API routes for user authentication endpoints."""

from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import AccessTokenBearer, RefreshTokenBearer, get_current_user
from app.core.config import settings
from app.core.security import create_access_token
from app.db.redis import add_token_to_blocklist
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    data: UserCreate, db: Annotated[AsyncSession, Depends(get_session)]
) -> UserRead:
    """Register a new user and return the created user."""
    return await AuthService.create_user(db, data)


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Token:
    """Authenticate a user and return access and refresh tokens."""
    user = await AuthService.authenticate_user(db, data.email, data.password)
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_access_token(
        subject=str(user.id),
        expiry=timedelta(days=settings.refresh_token_expire_days),
        refresh=True,
    )
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def revoke_access_token(
    token_details: Annotated[dict[str, Any], Depends(AccessTokenBearer())],
) -> None:
    """Logout the current user by revoking the access token."""
    await add_token_to_blocklist(token_details["jti"])
    return JSONResponse(
        content={"message": "Logged Out Successfully"}, status_code=status.HTTP_200_OK
    )


@router.get("/refresh-token", response_model=Token)
async def get_new_access_token(
    token_details: Annotated[dict[str, Any], Depends(RefreshTokenBearer())],
) -> Token:
    """Generate a new access token using a valid refresh token."""
    new_access_token = create_access_token(subject=token_details["sub"])
    return Token(access_token=new_access_token)


@router.get("/me", response_model=UserRead)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    """Get the current authenticated user."""
    return current_user

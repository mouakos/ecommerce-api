# mypy: disable-error-code=return-value

"""API routes for user authentication endpoints."""

from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import AccessTokenBearer, RefreshTokenBearer, get_current_user
from app.core.config import settings
from app.core.errors import (
    AccountNotVerifiedError,
    InvalidEmailTokenError,
    UserNotFoundError,
)
from app.core.security import create_access_token, create_url_safe_token, decode_url_safe_token
from app.db.redis import add_token_to_blocklist
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import EmailSchema, Token, UserCreate, UserLogin, UserRead
from app.services.auth_service import AuthService
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_new_user(
    data: UserCreate, db: Annotated[AsyncSession, Depends(get_session)]
) -> JSONResponse:
    """Register a new user and return the created user."""
    user = await AuthService.create_user(db, data)
    token = create_url_safe_token(user.email)

    await EmailService.send_verification_email([user.email], token)

    return JSONResponse(
        content={
            "message": "User registered successfully. Please check your email to verify your account."
        },
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Token:
    """Authenticate a user and return access and refresh tokens."""
    user = await AuthService.authenticate_user(db, data.email, data.password)
    if not user.is_verified:
        raise AccountNotVerifiedError()
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


@router.post("/verify/{token}", status_code=status.HTTP_200_OK)
async def verify_user_email(
    token: str, session: Annotated[AsyncSession, Depends(get_session)]
) -> JSONResponse:
    """Confirm a user's email using a token."""
    user_email = decode_url_safe_token(token)

    if user_email:
        await AuthService.verify_user_email(session, user_email)

        return JSONResponse(
            content={"message": "Email confirmed successfully"},
            status_code=status.HTTP_200_OK,
        )

    raise InvalidEmailTokenError()


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification_email(
    email_data: EmailSchema,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> JSONResponse:
    """Resend the email verification link to the current user."""
    user = await AuthService.get_user_by_email(db, email_data.address)
    if not user:
        raise UserNotFoundError()

    if user.is_verified:
        return JSONResponse(
            content={"message": "Account is already verified."},
            status_code=status.HTTP_200_OK,
        )
    token = create_url_safe_token(user.email)

    await EmailService.send_verification_email([email_data.address], token)

    return JSONResponse(
        content={"message": "Verification email resent successfully. Please check your email."},
        status_code=status.HTTP_200_OK,
    )

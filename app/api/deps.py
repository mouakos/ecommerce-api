"""API Routes dependencies."""

from abc import ABC, abstractmethod
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import (
    AccessTokenRequiredError,
    InsufficientPermissionError,
    InvalidTokenError,
    RefreshTokenRequiredError,
    RevokedTokenError,
)
from app.core.security import decode_token
from app.db.redis import is_token_in_blocklist
from app.db.session import get_session
from app.models.user import User


class TokenBearer(HTTPBearer, ABC):
    """Abstract Bearer class to verify tokens."""

    def __init__(self) -> None:
        """Initialize the TokenBearer."""
        super().__init__()

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        """Call method to verify the token."""
        http_auth_credentials = await super().__call__(request)
        assert http_auth_credentials is not None

        token = http_auth_credentials.credentials

        token_details = decode_token(token)

        if not self.token_valid(token):
            raise InvalidTokenError("Invalid token.")

        assert token_details is not None

        if await is_token_in_blocklist(token_details["jti"]):
            raise RevokedTokenError()

        self.verify_token_data(token_details)

        return token_details  # type: ignore [return-value]

    def token_valid(self, token: str) -> bool:
        """Check if the token is valid."""
        token_details = decode_token(token)

        return token_details is not None

    @abstractmethod
    def verify_token_data(self, token_details: dict[str, Any]) -> None:
        """Verify the token data."""
        pass


class AccessTokenBearer(TokenBearer):
    """Bearer class to verify access tokens."""

    def verify_token_data(self, token_details: dict[str, Any]) -> None:
        """Verify that the token is an access token."""
        if token_details and token_details["refresh"]:
            raise AccessTokenRequiredError()


class RefreshTokenBearer(TokenBearer):
    """Bearer class to verify refresh tokens."""

    def verify_token_data(self, token_details: dict[str, Any]) -> None:
        """Verify that the token is a refresh token."""
        if token_details and not token_details["refresh"]:
            raise RefreshTokenRequiredError()


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_session)],
    token_details: Annotated[dict[str, Any], Depends(AccessTokenBearer())],
) -> User:
    """Get the current user from the token.

    Args:
        db (Annotated[AsyncSession, Depends): Database session.
        token_details (dict[str, Any]): The decoded token data.

    Raises:
        UnauthorizedError: If the token is invalid or expired or if the user is inactive or missing.

    Returns:
        User: The current user.
    """
    user = await db.get(User, UUID(token_details["sub"]))
    if not user:
        raise InvalidTokenError()
    return user


class RoleChecker:
    """Dependency to check if the current user has one of the allowed roles."""

    def __init__(self, allowed_roles: list[str]) -> None:
        """Initialize the RoleChecker with allowed roles."""
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Annotated[User, Depends(get_current_user)]) -> bool:
        """Check if the current user has one of the allowed roles."""
        if current_user.role in self.allowed_roles:
            return True

        raise InsufficientPermissionError()

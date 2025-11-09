"""API Routes dependencies."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_session)],
    token: str = Depends(oauth2_scheme),
) -> User:
    """Get the current user from the token.

    Args:
        db (Annotated[AsyncSession, Depends): Database session.
        token (str, optional): Bearer token. Defaults to Depends(oauth2_scheme).

    Raises:
        UnauthorizedError: If the token is invalid or expired or if the user is inactive or missing.

    Returns:
        User: The current user.
    """
    payload = decode_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token.")
    user_id = UUID(payload.get("sub"))

    user = await db.get(User, user_id)
    if not user:
        raise UnauthorizedError("Invalid or expired token.")
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

        raise UnauthorizedError("Insufficient permissions.")

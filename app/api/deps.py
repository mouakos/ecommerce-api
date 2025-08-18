"""API Routes dependencies."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

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
    try:
        payload = decode_token(token)
        user_id = UUID(payload.get("sub"))
    except Exception as err:
        raise UnauthorizedError("Invalid or expired token.") from err

    user = await db.get(User, user_id)
    if not user:
        raise UnauthorizedError("Invalid or expired token.")
    return user

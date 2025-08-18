"""Security utilities for handling passwords and JWT tokens."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Generate a hashed password."""
    return pwd_context.hash(password)  # type: ignore[no-any-return]


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain (str): The plain password to verify.
        hashed (str): The hashed password to compare against.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain, hashed)  # type: ignore[no-any-return]


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Create a new access token.

    Args:
        subject (str): The subject for the token, typically the user ID.
        expires_minutes (int | None, optional): The expiration time in minutes. Defaults to None.

    Returns:
        str: The encoded JWT token.
    """
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)  # type: ignore[no-any-return]


def decode_token(token: str) -> dict[str, Any]:
    """Decode a JWT token.

    Args:
        token (str): The JWT token to decode.

    Returns:
        dict[str, Any]: The decoded token payload.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])  # type: ignore[no-any-return]

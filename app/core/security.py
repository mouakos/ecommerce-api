"""Security utilities for handling passwords and JWT tokens."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.enums import TokenType

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Generate a hashed password."""
    return str(pwd_context.hash(password))


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain (str): The plain password to verify.
        hashed (str): The hashed password to compare against.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return bool(pwd_context.verify(plain, hashed))


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Create a new access token.

    Args:
        subject (str): The subject for the token, typically the user ID.
        expires_minutes (int | None, optional): The expiration time in minutes. Defaults to None.

    Returns:
        str: The encoded JWT token.
    """
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload = {"sub": str(subject), "exp": expire, "token_type": TokenType.ACCESS}
    return str(jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm))


def create_refresh_token(subject: str, expires_days: int | None = None) -> str:
    """Create a new refresh token.

    Args:
        subject (str): The subject for the token, typically the user ID.
        expires_days (int | None, optional): The expiration time in days. Defaults to None.

    Returns:
        str: The encoded JWT token.
    """
    expire = datetime.now(UTC) + timedelta(days=expires_days or settings.refresh_token_expire_days)
    payload = {"sub": str(subject), "exp": expire, "token_type": TokenType.REFRESH}
    return str(jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm))


def verify_token_type(token: str, expected_type: TokenType) -> str | None:
    """Verify that the token is of the expected type.

    Args:
        token (str): The JWT token to verify.
        expected_type (TokenType): The expected token type.

    Returns:
        str | None: The subject if the token type matches, None otherwise.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("token_type") == expected_type and payload.get("sub"):
            return str(payload.get("sub"))
        return None
    except JWTError:
        return None

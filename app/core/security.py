"""Security utilities for handling passwords and JWT tokens."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from itsdangerous import URLSafeTimedSerializer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeTimedSerializer(secret_key=settings.secret_key, salt="email-configuration")


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


def create_access_token(
    subject: str, expiry: timedelta | None = None, refresh: bool = False
) -> str:
    """Create a new access token.

    Args:
        subject (str): The subject for the token, typically the user ID.
        expiry (timedelta, optional): Expiration time as a timedelta. Defaults to None.
        refresh (bool, optional): Whether the token is a refresh token. Defaults to False.

    Returns:
        str: The encoded JWT token.
    """
    expire = datetime.now(UTC) + (expiry or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {
        "sub": str(subject),
        "exp": expire,
        "jti": str(uuid4()),
        "refresh": refresh,
    }
    return str(jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm))


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode a JWT token without verification.

    Args:
        token (str): The JWT token to decode.

    Returns:
        dict[str, Any] | None: The decoded payload or None if decoding fails.
    """
    try:
        return jwt.decode(token, settings.secret_key, [settings.jwt_algorithm])  # type: ignore [no-any-return]
    except JWTError as e:
        logging.error(str(e))
        return None


def create_url_safe_token(user_email: str) -> str:
    """Create a URL-safe token for email verification or password reset."""
    return str(serializer.dumps(user_email))


def decode_url_safe_token(private_key: str, max_age=1800) -> str | None:
    """Decode a URL-safe token."""
    try:
        return str(serializer.loads(private_key, max_age=max_age))
    except Exception as e:
        logging.error(str(e))
        return None

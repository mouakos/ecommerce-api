"""Redis connection and token blocklist management."""

import aioredis

from app.core.config import settings

token_blocklist = aioredis.StrictRedis(host=settings.redis_host, port=settings.redis_port, db=0)

JTI_EXPIRY = 3600  # seconds (1 hour)


async def is_token_in_blocklist(jti: str) -> bool:
    """Check if a token has been revoked.

    Args:
        jti (str): The unique identifier of the token.

    Returns:
        bool: True if the token is revoked, False otherwise.
    """
    is_revoked = await token_blocklist.get(jti)
    return is_revoked is not None


async def add_token_to_blocklist(jti: str) -> None:
    """Revoke a token by adding its JTI to the blocklist.

    Args:
        jti (str): The unique identifier of the token.
    """
    await token_blocklist.set(jti, "revoked", ex=JTI_EXPIRY)

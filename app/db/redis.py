"""Redis connection and token blocklist management."""

from redis.asyncio import Redis

from app.core.config import settings

JTI_EXPIRY = 3600  # seconds (1 hour)


def get_redis() -> Redis:
    """Create a new Redis client instance.

    Returns:
        Redis: A Redis asyncio client.
    """
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def is_token_in_blocklist(jti: str) -> bool:
    """Check if a token has been revoked.

    Args:
        jti (str): The unique identifier of the token.

    Returns:
        bool: True if the token is revoked, False otherwise.
    """
    redis = get_redis()
    is_revoked = await redis.get(jti)
    await redis.close()
    return is_revoked is not None


async def add_token_to_blocklist(jti: str) -> None:
    """Revoke a token by adding its JTI to the blocklist.

    Args:
        jti (str): The unique identifier of the token.
    """
    redis = get_redis()
    await redis.set(jti, value="", ex=JTI_EXPIRY)
    await redis.close()

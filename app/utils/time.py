"""Time-related helpers for the application."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return UTC timestamp."""
    return datetime.now(UTC).replace(tzinfo=None)

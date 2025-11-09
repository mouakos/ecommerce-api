"""Enums for the application."""

from enum import StrEnum


class TokenType(StrEnum):
    """Enum for token types."""

    ACCESS = "access"
    REFRESH = "refresh"

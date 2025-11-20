"""Enumerations for user roles and order statuses."""

from enum import StrEnum


class UserRole(StrEnum):
    """Enumeration for user roles."""

    ADMIN = "admin"
    USER = "user"


class OrderStatus(StrEnum):
    """Enumeration for order statuses."""

    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"

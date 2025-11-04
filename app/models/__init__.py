"""Eagerly import all SQLModel classes to register relationships safely.

External code can now simply:

    from app.models import Product, CartItem

without worrying about partial registration of related models.
"""

from .cart import Cart, CartItem  # noqa: F401
from .category import Category  # noqa: F401
from .order import Order, OrderItem  # noqa: F401
from .product import Product  # noqa: F401
from .review import Review  # noqa: F401
from .user import User  # noqa: F401

__all__ = [
    "User",
    "Category",
    "Cart",
    "CartItem",
    "Order",
    "OrderItem",
    "Review",
    "Product",
]

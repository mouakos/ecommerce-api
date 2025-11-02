"""Order service for managing user orders."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.cart_service import CartService


def _order_number(order_id: UUID) -> str:
    return f"ORD-{str(order_id)[:8].upper()}"


class OrderService:
    """Service for managing orders."""

    @staticmethod
    async def checkout(user_id: UUID, db: AsyncSession) -> Order:
        """Checkout the user's cart and create an order.

        Args:
            user_id (UUID): The ID of the user.
            db (AsyncSession): The database session.

        Raises:
            ConflictError: If there is a stock conflict.
            NotFoundError: If the cart is not found.

        Returns:
            Order: The created order.
        """
        # 1) Load cart with items
        cart = await CartService.get_user_cart(user_id, db)

        if not cart or not cart.items:
            raise BadRequestError("Cart is empty.")

        # 2) Lock all product rows we'll touch
        product_ids = [it.product_id for it in cart.items]
        products = (
            (
                await db.execute(
                    select(Product)
                    .where(Product.id.in_(product_ids))  # type: ignore[attr-defined]
                    .with_for_update()  # row-level locks
                )
            )
            .scalars()
            .all()
        )
        products_by_id = {p.id: p for p in products}

        # 3) Validate stock
        for it in cart.items:
            p = products_by_id.get(it.product_id)
            if not p or it.quantity > p.stock:
                raise ConflictError("Not enough stock.")

        # 4) Create order + items, decrement stock (single transaction)
        order = Order(
            user_id=user_id, number="temp", total_amount=0
        )  # temp; update after id assigned
        db.add(order)
        await db.flush()  # get order.id

        order.number = _order_number(order.id)

        total = 0.0
        for it in cart.items:
            p = products_by_id[it.product_id]
            p.stock -= it.quantity
            oi = OrderItem(
                order_id=order.id,
                product_id=it.product_id,
                quantity=it.quantity,
                unit_price=it.unit_price,  # snapshot from cart
            )
            db.add(oi)
            total += it.quantity * float(it.unit_price)
        order.total_amount = total

        # Delete the cart (cascade removes items)
        await db.delete(cart)

        await db.flush()
        # Reload with items for response
        await db.refresh(order)
        return order

    @staticmethod
    async def list_user_orders(user_id: UUID, db: AsyncSession) -> list[Order]:
        """List all orders for a user.

        Args:
            user_id (UUID): The ID of the user.
            db (AsyncSession): The database session.

        Returns:
            list[Order]: The list of orders.
        """
        res = await db.execute(
            select(Order).where(Order.user_id == user_id).order_by(desc(Order.created_at))  # type: ignore[arg-type]
        )

        return list(res.scalars())

    @staticmethod
    async def get_user_order(user_id: UUID, order_id: UUID, db: AsyncSession) -> Order:
        """Get a specific order for a user, loading items.

        Args:
            user_id (UUID): The ID of the user.
            order_id (UUID): The ID of the order.
            db (AsyncSession): The database session.

        Raises:
            NotFoundError: If the order is not found.

        Returns:
            Order: The order.
        """
        res = await db.execute(
            select(Order).where((Order.id == order_id) & (Order.user_id == user_id))  # type: ignore[arg-type]
        )
        order = res.scalar_one_or_none()
        if not order:
            raise NotFoundError(f"Order {order_id} not found for user {user_id}")
        return order

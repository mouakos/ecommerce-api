"""Order service for managing user orders."""

from uuid import UUID

from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.enums import OrderStatus
from app.core.errors import EmptyCartError, InsufficientStockError, OrderNotFoundError
from app.models.address import Address
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.cart_service import CartService


def _order_number(order_id: UUID) -> str:
    return f"ORD-{str(order_id)[:8].upper()}"


class OrderService:
    """Service for managing orders."""

    # Allowed status transitions (source -> set of permitted next statuses)
    _ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
        OrderStatus.PENDING: {OrderStatus.PROCESSING, OrderStatus.CANCELED},
        OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELED},
        OrderStatus.SHIPPED: {OrderStatus.DELIVERED, OrderStatus.RETURNED},
        OrderStatus.DELIVERED: {OrderStatus.RETURNED, OrderStatus.REFUNDED},
        OrderStatus.RETURNED: {OrderStatus.REFUNDED},
        # Terminal states (no further transitions)
        OrderStatus.CANCELED: set(),
        OrderStatus.REFUNDED: set(),
    }

    @staticmethod
    async def checkout(
        user_id: UUID,
        db: AsyncSession,
        *,
        shipping_address_id: UUID | None = None,
        billing_address_id: UUID | None = None,
    ) -> Order:
        """Checkout the user's cart and create an order.

        Args:
            user_id (UUID): The ID of the user.
            db (AsyncSession): The database session.
            shipping_address_id (UUID | None): Optional shipping address UUID.
            billing_address_id (UUID | None): Optional billing address UUID.

        Raises:
            EmptyCartError: If the user's cart is empty.
            InsufficientStockError: If any product lacks sufficient stock.

        Returns:
            Order: The created order.
        """
        # 1) Load cart with items
        cart = await CartService.get_user_cart(user_id, db)

        if not cart or not cart.items:
            raise EmptyCartError()

        # 2) Lock all product rows we'll touch
        product_ids = [it.product_id for it in cart.items]
        products = (
            await db.exec(
                select(Product)
                .where(Product.id.in_(product_ids))  # type: ignore[attr-defined]
                .with_for_update()  # row-level locks
            )
        ).all()
        products_by_id = {p.id: p for p in products}

        # 3) Validate stock
        for it in cart.items:
            p = products_by_id.get(it.product_id)
            if not p or it.quantity > p.stock:
                raise InsufficientStockError()

        # 4) Validate address ownership (if provided)
        async def _load_address(addr_id: UUID | None) -> Address | None:
            return None if not addr_id else await db.get(Address, addr_id)

        shipping_addr = await _load_address(shipping_address_id)
        if shipping_address_id and (not shipping_addr or shipping_addr.user_id != user_id):
            from app.core.errors import AddressNotFoundError

            raise AddressNotFoundError()

        billing_addr = await _load_address(billing_address_id)
        if billing_address_id and (not billing_addr or billing_addr.user_id != user_id):
            from app.core.errors import AddressNotFoundError

            raise AddressNotFoundError()

        # 5) Create order + items, decrement stock (single transaction)
        order = Order(
            user_id=user_id,
            number="temp",
            total_amount=0,
            shipping_address_id=shipping_address_id,
            billing_address_id=billing_address_id,
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
        res = await db.exec(
            select(Order).where(Order.user_id == user_id).order_by(desc(Order.created_at))
        )

        return list(res.all())

    @staticmethod
    async def get_user_order(user_id: UUID, order_id: UUID, db: AsyncSession) -> Order:
        """Get a specific order for a user.

        Args:
            user_id (UUID): The ID of the user.
            order_id (UUID): The ID of the order.
            db (AsyncSession): The database session.

        Raises:
            OrderNotFoundError: If the order does not exist for the user.

        Returns:
            Order: The order.
        """
        stmt = select(Order).where(Order.id == order_id).where(Order.user_id == user_id)
        order = (await db.exec(stmt)).first()
        if not order:
            raise OrderNotFoundError()
        return order

    @staticmethod
    async def update_order_status(
        order_id: UUID, new_status: OrderStatus, db: AsyncSession
    ) -> Order:
        """Update the status of an order enforcing allowed transitions.

        Args:
            order_id (UUID): The ID of the order.
            new_status (OrderStatus): The new status to set.
            db (AsyncSession): The database session.

        Raises:
            OrderNotFoundError: If the order does not exist.

        Returns:
            Order: The updated order.
        """
        stmt = select(Order).where(Order.id == order_id)
        order = (await db.exec(stmt)).first()
        if not order:
            raise OrderNotFoundError()

        current = order.status
        allowed = OrderService._ALLOWED_TRANSITIONS.get(current, set())
        # If trying to set same status, just return (idempotent)
        if new_status == current:
            return order
        if new_status not in allowed:
            from app.core.errors import InvalidOrderStatusTransitionError

            raise InvalidOrderStatusTransitionError()
        order.status = new_status
        db.add(order)
        await db.flush()
        await db.refresh(order)
        return order

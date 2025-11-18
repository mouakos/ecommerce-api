"""Cart service for managing shopping cart operations in the application."""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import (
    CartItemNotFoundError,
    InsufficientStockError,
)
from app.models.cart import Cart, CartItem
from app.schemas.cart import CartItemCreate
from app.services.product_service import ProductService


class CartService:
    """Service for managing shopping cart operations."""

    @staticmethod
    async def get_user_cart(user_id: UUID, db: AsyncSession) -> Cart | None:
        """Get the cart for a specific user.

        Args:
            user_id (UUID): User ID.
            db (AsyncSession): Database session.

        Returns:
            Cart | None: User cart or None.
        """
        res = await db.exec(select(Cart).where(Cart.user_id == user_id))
        return res.first()

    @staticmethod
    async def get_or_create_user_cart(user_id: UUID, db: AsyncSession) -> Cart:
        """Get or create a cart for a user.

        Args:
            user_id (UUID): User ID.
            db (AsyncSession): Database session.

        Returns:
            Cart: Existing or new cart.
        """
        cart = await CartService.get_user_cart(user_id, db)
        if cart:
            return cart
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.flush()
        await db.refresh(cart)
        return cart

    @staticmethod
    async def clear_user_cart(user_id: UUID, db: AsyncSession) -> None:
        """Clear a user's cart.

        Args:
            user_id (UUID): User ID.
            db (AsyncSession): Database session.
        """
        cart = await CartService.get_user_cart(user_id, db)
        if not cart:
            return
        await db.delete(cart)
        await db.flush()

    @staticmethod
    async def add_item_to_user_cart(user_id: UUID, data: CartItemCreate, db: AsyncSession) -> Cart:
        """Add an item to the user's cart.

        Args:
            user_id (UUID): User ID.
            data (CartItemCreate): Item data.
            db (AsyncSession): Database session.

        Raises:
            ProductNotFoundError: If the product does not exist.
            InsufficientStockError: If requested quantity exceeds stock.

        Returns:
            Cart: Updated cart.
        """
        cart = await CartService.get_or_create_user_cart(user_id, db)

        product = await ProductService.get(data.product_id, db)

        res = await db.exec(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product.id)
        )
        item = res.first()
        current_qty = item.quantity if item else 0
        new_qty = current_qty + data.quantity

        if new_qty > product.stock:
            raise InsufficientStockError()

        if item:
            item.quantity = new_qty
        else:
            item = CartItem(
                cart_id=cart.id,
                product_id=product.id,
                quantity=data.quantity,
                unit_price=product.price,
            )
            db.add(item)

        await db.flush()
        await db.refresh(cart)
        return cart

    @staticmethod
    async def update_item_to_user_cart(
        user_id: UUID, item_id: UUID, quantity: int | None, db: AsyncSession
    ) -> Cart:
        """Update quantity of an item in the user's cart.

        Args:
            user_id (UUID): User ID.
            item_id (UUID): Cart item ID.
            quantity (int | None): New quantity (None => no change).
            db (AsyncSession): Database session.

        Raises:
            CartItemNotFoundError: If the item is not in the user's cart.
            ProductNotFoundError: If the related product does not exist.
            InsufficientStockError: If requested quantity exceeds stock.

        Returns:
            Cart: Updated cart.
        """
        cart = await CartService.get_or_create_user_cart(user_id, db)

        item = await db.get(CartItem, item_id)
        if not item or item.cart_id != cart.id:
            raise CartItemNotFoundError()

        if quantity is None:
            return cart

        if quantity <= 0:
            await db.delete(item)
            await db.flush()
            await db.refresh(cart)
            return cart

        product = await ProductService.get(item.product_id, db)
        if quantity > product.stock:
            raise InsufficientStockError()

        item.quantity = quantity
        await db.flush()
        await db.refresh(cart)
        return cart

    @staticmethod
    async def remove_item_from_user_cart(user_id: UUID, item_id: UUID, db: AsyncSession) -> None:
        """Remove an item from a user's cart.

        Args:
            user_id (UUID): User ID.
            item_id (UUID): Cart item ID.
            db (AsyncSession): Database session.

        Raises:
            CartItemNotFoundError: If the item is not in the user's cart.
        """
        cart = await CartService.get_user_cart(user_id, db)
        if not cart:
            return

        item = await db.get(CartItem, item_id)
        if not item or item.cart_id != cart.id:
            raise CartItemNotFoundError()

        await db.delete(item)
        await db.flush()

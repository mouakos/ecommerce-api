"""Cart service for managing shopping cart operations in the application."""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import CartItemNotFoundError, CartNotFoundError, InsufficientStockError
from app.models.cart import Cart, CartItem
from app.schemas.cart import CartItemCreate
from app.services.product_service import ProductService


class CartService:
    """Service for managing shopping cart operations."""

    @staticmethod
    async def get_user_cart(user_id: UUID, db: AsyncSession) -> Cart | None:
        """Get the cart for a specific user.

        Args:
            user_id (UUID): The ID of the user to retrieve the cart for.
            db (AsyncSession): The database session to use.

        Returns:
            Cart | None: The cart for the user, or None if not found.
        """
        res = await db.exec(select(Cart).where(Cart.user_id == user_id))
        return res.first()

    @staticmethod
    async def get_or_create_user_cart(user_id: UUID, db: AsyncSession) -> Cart:
        """Get or create a cart for a specific user.

        Args:
            user_id (UUID): The ID of the user to retrieve or create the cart for.
            db (AsyncSession): The database session to use.

        Returns:
            Cart: The cart for the user.
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
        """Clear the cart for a specific user.

        Args:
            user_id (UUID): The ID of the user to clear the cart for.
            db (AsyncSession): The database session to use.
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
            user_id (UUID): The ID of the user who owns the cart.
            data (CartItemCreate): The data for the cart item to add.
            db (AsyncSession): The database session to use.

        Raises:
            NotFoundError: If product is not found.
            ConflictError: If there is not enough stock for the item.

        Returns:
            Cart : The updated cart.
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
                unit_price=product.price,  # snapshot
            )
            db.add(item)

        await db.flush()
        await db.refresh(cart)
        return cart

    @staticmethod
    async def update_item_to_user_cart(
        user_id: UUID, item_id: UUID, quantity: int | None, db: AsyncSession
    ) -> Cart:
        """Update the quantity of an item in the user's cart.

        Args:
            user_id (UUID): The ID of the user who owns the cart.
            item_id (UUID): The ID of the item to update.
            quantity (int | None): The new quantity for the item.
            db (AsyncSession): The database session to use.

        Raises:
            NotFoundError: If item is not found.
            ConflictError: If there is not enough stock for the item.

        Returns:
            Cart: The updated cart.
        """
        cart = await CartService.get_or_create_user_cart(user_id, db)

        item = await db.get(CartItem, item_id)
        if not item or item.cart_id != cart.id:
            raise CartNotFoundError()

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
            user_id (UUID): The ID of the user who owns the cart.
            item_id (UUID): The ID of the item to remove.
            db (AsyncSession): The database session to use.

        Raises:
            NotFoundError: If the cart or item is not found.
        """
        cart = await CartService.get_user_cart(user_id, db)
        if not cart:
            return

        item = await db.get(CartItem, item_id)
        if not item or item.cart_id != cart.id:
            raise CartItemNotFoundError()

        await db.delete(item)
        await db.flush()

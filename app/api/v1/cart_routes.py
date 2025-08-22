# mypy: disable-error-code=return-value

"""API routes for shopping cart endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead
from app.services.cart_service import CartService

router = APIRouter(prefix="/api/v1/cart", tags=["Cart"])


@router.get("/", response_model=CartRead)
async def get_my_cart(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CartRead:
    """Get or create a cart for the current user."""
    return await CartService.get_or_create_user_cart(current_user.id, db)


@router.post("/items", response_model=CartRead)
async def add_item_to_my_cart(
    data: CartItemCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CartRead:
    """Add an item to the user's cart."""
    return await CartService.add_item_to_user_cart(current_user.id, data, db)


@router.put("/items/{item_id}", response_model=CartRead)
async def update_my_cart_item(
    item_id: UUID,
    data: CartItemUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CartRead:
    """Update an item in the user's cart."""
    return await CartService.update_item_to_user_cart(current_user.id, item_id, data.quantity, db)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_my_cart_item(
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Remove an item from the user's cart."""
    await CartService.remove_item_from_user_cart(current_user.id, item_id, db)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_my_cart(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Clear the current user's cart."""
    await CartService.clear_user_cart(current_user.id, db)

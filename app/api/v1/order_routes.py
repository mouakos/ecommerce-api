# mypy: disable-error-code=return-value

"""API routes for order endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.order import OrderRead
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def checkout(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> OrderRead:
    """Checkout the user's cart and create an order."""
    return await OrderService.checkout(current_user.id, db)


@router.get("/", response_model=list[OrderRead])
async def list_my_orders(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[OrderRead]:
    """List all orders for the current user."""
    return await OrderService.list_user_orders(current_user.id, db)


@router.get("/{order_id}", response_model=OrderRead)
async def get_my_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> OrderRead:
    """Get a specific order for the current user by order ID."""
    return await OrderService.get_user_order(current_user.id, order_id, db)

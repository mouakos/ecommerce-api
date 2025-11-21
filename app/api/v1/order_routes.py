# mypy: disable-error-code=return-value

"""API routes for order endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import RoleChecker, get_current_user
from app.core.enums import UserRole
from app.db.session import get_session
from app.models.user import User
from app.schemas.order import OrderAddress, OrderRead, OrderStatusUpdate
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])
role_checker = Depends(RoleChecker([UserRole.ADMIN]))


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def checkout(
    order_address: OrderAddress,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> OrderRead:
    """Checkout the user's cart and create an order."""
    return await OrderService.checkout(
        current_user.id,
        order_address=order_address,
        db=db,
    )


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


@router.patch("/{order_id}/status", response_model=OrderRead, dependencies=[role_checker])
async def update_order_status(
    order_id: UUID,
    order_status_update: OrderStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> OrderRead:
    """Update the status of an order."""
    return await OrderService.update_order_status(order_id, order_status_update.status, db)

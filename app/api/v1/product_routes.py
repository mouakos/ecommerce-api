"""API routes for product endpoints."""

# mypy: disable-error-code=return-value
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.get("/", response_model=list[ProductRead])
async def list_products(db: Annotated[AsyncSession, Depends(get_session)]) -> list[ProductRead]:
    """List all products."""
    return await ProductService.list(db)


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate, db: Annotated[AsyncSession, Depends(get_session)]
) -> ProductRead:
    """Create a new product."""
    return await ProductService.create(data, db)


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: UUID, db: Annotated[AsyncSession, Depends(get_session)]
) -> ProductRead:
    """Get a product by its ID."""
    return await ProductService.get(product_id, db)


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: UUID, data: ProductUpdate, db: Annotated[AsyncSession, Depends(get_session)]
) -> ProductRead:
    """Update an existing product by its ID."""
    return await ProductService.update(product_id, data, db)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID, db: Annotated[AsyncSession, Depends(get_session)]
) -> None:
    """Delete a product by its ID."""
    await ProductService.delete(product_id, db)

"""API routes for product endpoints."""

# mypy: disable-error-code=return-value
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import RoleChecker
from app.db.session import get_session
from app.schemas.base import Page
from app.schemas.product import ProductCreate, ProductRead, ProductReadDetail, ProductUpdate
from app.schemas.review import AverageReview
from app.services.product_service import ProductService
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api/v1/products", tags=["Products"])
role_checker = Depends(RoleChecker(["admin"]))


@router.get("/", response_model=Page[ProductRead])
async def list_products(
    db: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, description="Search name/description (case-insensitive)"),
    category_id: UUID | None = None,
    price_min: float | None = Query(None, ge=0),
    price_max: float | None = Query(None, ge=0),
    in_stock: bool | None = Query(None, description="True: stock>0, False: stock==0"),
    order_by: Literal["name", "price", "created_at", "updated_at"] = Query("name"),
    order_dir: Literal["asc", "desc"] = Query("asc"),
) -> Page[ProductRead]:
    """List all products."""
    items, total = await ProductService.list(
        db,
        limit=limit,
        offset=offset,
        search=search,
        category_id=category_id,
        price_min=price_min,
        price_max=price_max,
        in_stock=in_stock,
        order_by=order_by,
        order_dir=order_dir,
    )
    return Page[ProductRead](items=items, total=total, limit=limit, offset=offset)


@router.get("/{product_id}/reviews/summary", response_model=AverageReview)
async def get_product_review_summary(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AverageReview:
    """Get average rating and review count for a product."""
    avg, count = await ReviewService.average(product_id, db)
    return AverageReview(average_rating=avg, review_count=count)


@router.post(
    "/",
    response_model=ProductReadDetail,
    status_code=status.HTTP_201_CREATED,
    dependencies=[role_checker],
)
async def create_product(
    data: ProductCreate, db: Annotated[AsyncSession, Depends(get_session)]
) -> ProductReadDetail:
    """Create a new product."""
    return await ProductService.create(data, db)


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: UUID, db: Annotated[AsyncSession, Depends(get_session)]
) -> ProductRead:
    """Get a product by its ID."""
    return await ProductService.get(product_id, db)


@router.put("/{product_id}", response_model=ProductRead, dependencies=[role_checker])
async def update_product(
    product_id: UUID, data: ProductUpdate, db: Annotated[AsyncSession, Depends(get_session)]
) -> ProductRead:
    """Update an existing product by its ID."""
    return await ProductService.update(product_id, data, db)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[role_checker])
async def delete_product(
    product_id: UUID, db: Annotated[AsyncSession, Depends(get_session)]
) -> None:
    """Delete a product by its ID."""
    await ProductService.delete(product_id, db)

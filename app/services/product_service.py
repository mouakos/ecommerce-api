# mypy: disable-error-code=arg-type
"""Service layer for product-related business logic in the ecommerce API."""

from typing import Literal
from uuid import UUID

from sqlmodel import asc, desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import (
    ProductAlreadyExistsError,
    ProductNotFoundError,
)
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.category_service import CategoryService

OrderBy = Literal["name", "price", "created_at", "updated_at"]
OrderDir = Literal["asc", "desc"]


class ProductService:
    """Service for managing products."""

    @staticmethod
    async def list(
        db: AsyncSession,
        limit: int,
        offset: int,
        search: str | None = None,
        category_id: UUID | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        in_stock: bool | None = None,
        order_by: OrderBy = "name",
        order_dir: OrderDir = "asc",
    ) -> tuple[list[Product], int]:
        """List products with filtering and pagination.

        Args:
            db (AsyncSession): Database session.
            limit (int): Page size.
            offset (int): Offset.
            search (str | None): Text search.
            category_id (UUID | None): Category filter.
            price_min (float | None): Min price.
            price_max (float | None): Max price.
            in_stock (bool | None): Stock filter.
            order_by (OrderBy): Sort field.
            order_dir (OrderDir): Sort direction.

        Returns:
            tuple[list[Product], int]: Items and total count.
        """
        stmt = select(Product)
        count_stmt = select(func.count()).select_from(Product)

        if search:
            like = f"%{search.lower()}%"
            cond = func.lower(Product.name).like(like) | func.lower(Product.description).like(like)
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
            count_stmt = count_stmt.where(Product.category_id == category_id)

        if price_min is not None:
            stmt = stmt.where(Product.price >= price_min)
            count_stmt = count_stmt.where(Product.price >= price_min)

        if price_max is not None:
            stmt = stmt.where(Product.price <= price_max)
            count_stmt = count_stmt.where(Product.price <= price_max)

        if in_stock is True:
            stmt = stmt.where(Product.stock > 0)
            count_stmt = count_stmt.where(Product.stock > 0)
        elif in_stock is False:
            stmt = stmt.where(Product.stock == 0)
            count_stmt = count_stmt.where(Product.stock == 0)

        order_col = {
            "name": Product.name,
            "price": Product.price,
            "created_at": Product.created_at,
        }[order_by]
        order_col = desc(order_col) if order_dir == "desc" else asc(order_col)

        total = int((await db.exec(count_stmt)).first())
        res = await db.exec(stmt.order_by(order_col).limit(limit).offset(offset))
        items = list(res.all())
        return items, total

    @staticmethod
    async def create(product: ProductCreate, db: AsyncSession) -> Product:
        """Create a new product.

        Args:
            product (ProductCreate): Product data.
            db (AsyncSession): Database session.

        Raises:
            CategoryNotFoundError: If the category does not exist.
            ProductAlreadyExistsError: If a product with same name in category exists.

        Returns:
            Product: Created product.
        """
        _ = await CategoryService.get(product.category_id, db)

        existing_product = await ProductService.get_by_name_and_category(
            db, product.name, product.category_id
        )
        if existing_product:
            raise ProductAlreadyExistsError()

        db_product = Product(**product.model_dump())
        db.add(db_product)
        await db.flush()
        await db.refresh(db_product)
        return db_product

    @staticmethod
    async def get(product_id: UUID, db: AsyncSession) -> Product:
        """Get a product by its ID.

        Args:
            product_id (UUID): Product ID.
            db (AsyncSession): Database session.

        Raises:
            ProductNotFoundError: If the product does not exist.

        Returns:
            Product: Retrieved product.
        """
        product = await db.get(Product, product_id)
        if not product:
            raise ProductNotFoundError()
        return product

    @staticmethod
    async def update(product_id: UUID, product: ProductUpdate, db: AsyncSession) -> Product:
        """Update an existing product.

        Args:
            product_id (UUID): Product ID.
            product (ProductUpdate): Update data.
            db (AsyncSession): Database session.

        Raises:
            ProductNotFoundError: If the product does not exist.
            CategoryNotFoundError: If the new category does not exist.
            ProductAlreadyExistsError: If name/category combination duplicates another product.

        Returns:
            Product: Updated product.
        """
        db_product = await db.get(Product, product_id)
        if not db_product:
            raise ProductNotFoundError()

        product_category = db_product.category_id

        if product.category_id:
            _ = await CategoryService.get(product.category_id, db)
            product_category = product.category_id

        if product.name:
            existing_product = await ProductService.get_by_name_and_category(
                db, product.name, product_category
            )
            if existing_product and existing_product.id != db_product.id:
                raise ProductAlreadyExistsError()

        for key, value in product.model_dump(exclude_unset=True).items():
            setattr(db_product, key, value)

        await db.flush()
        await db.refresh(db_product)
        return db_product

    @staticmethod
    async def delete(product_id: UUID, db: AsyncSession) -> None:
        """Delete a product by its ID.

        Args:
            product_id (UUID): Product ID.
            db (AsyncSession): Database session.

        Raises:
            ProductNotFoundError: If the product does not exist.
        """
        db_product = await db.get(Product, product_id)
        if not db_product:
            raise ProductNotFoundError()

        await db.delete(db_product)
        await db.flush()

    @staticmethod
    async def get_by_name_and_category(
        db: AsyncSession, product_name: str, category_id: UUID
    ) -> Product | None:
        """Get a product by name and category.

        Args:
            db (AsyncSession): Database session.
            product_name (str): Product name.
            category_id (UUID): Category ID.

        Returns:
            Product | None: Matching product or None.
        """
        stmt = select(Product).where(
            (Product.name == product_name) & (Product.category_id == category_id)
        )
        result = await db.exec(stmt)
        return result.first()

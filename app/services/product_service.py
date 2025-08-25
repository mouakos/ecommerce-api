# mypy: disable-error-code=arg-type

"""Service layer for product-related business logic in the ecommerce API."""

from typing import Literal
from uuid import UUID

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
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
        """List all products.

        Args:
            db (AsyncSession): The database session.
            limit (int): The maximum number of products to return.
            offset (int): The number of products to skip before starting to collect the result set.
            search (str | None): A search term to filter products by name or description.
            category_id (UUID | None): The ID of the category to filter products by.
            price_min (float | None): The minimum price to filter products by.
            price_max (float | None): The maximum price to filter products by.
            in_stock (bool | None): Whether to filter products by stock availability.
            order_by (OrderBy): The field to order the results by.
            order_dir (OrderDir): The direction to order the results (ascending or descending).

        Returns:
            list[Product]: A list of all products.
        """
        stmt = select(Product)
        count_stmt = select(func.count()).select_from(Product)

        # Filters
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

        # Sorting
        order_col = {
            "name": Product.name,
            "price": Product.price,
            "created_at": Product.created_at,
        }[order_by]
        order_col = desc(order_col) if order_dir == "desc" else asc(order_col)

        # Total first
        total = int((await db.execute(count_stmt)).scalar_one())

        # Page
        res = await db.execute(stmt.order_by(order_col).limit(limit).offset(offset))
        items = list(res.scalars().all())
        return items, total

    @staticmethod
    async def create(product: ProductCreate, db: AsyncSession) -> Product:
        """Create a new product.

        Args:
            product (ProductCreate): The product data to create.
            db (AsyncSession): The database session.

        Raises:
            ConflictError: If a product with the same name and category already exists.

        Returns:
            Product: The created product.
        """
        # Ensure the category exists
        _ = await CategoryService.get(product.category_id, db)

        existing_product = await ProductService.get_by_name_and_category(
            db, product.name, product.category_id
        )
        if existing_product:
            raise ConflictError("Product with this name already exists in the category.")

        db_product = Product(**product.model_dump())
        db.add(db_product)
        await db.commit()
        await db.refresh(db_product)
        return db_product

    @staticmethod
    async def get(product_id: UUID, db: AsyncSession) -> Product:
        """Get a product by its ID.

        Args:
            product_id (UUID): The ID of the product to retrieve.
            db (AsyncSession): The database session.

        Raises:
            NotFoundError: If the product is not found.

        Returns:
            Product: The retrieved product.
        """
        product = await db.get(Product, product_id)
        if not product:
            raise NotFoundError("Product not found.")
        return product

    @staticmethod
    async def update(product_id: UUID, product: ProductUpdate, db: AsyncSession) -> Product:
        """Update an existing product.

        Args:
            product_id (UUID): The ID of the product to update.
            product (ProductUpdate): The updated product data.
            db (AsyncSession): The database session.

        Raises:
            NotFoundError: If the product is not found.

        Returns:
            Product: The updated product.
        """
        db_product = await db.get(Product, product_id)
        if not db_product:
            raise NotFoundError("Product not found.")

        product_category = db_product.category_id

        # Ensure the category exists
        if product.category_id:
            _ = await CategoryService.get(product.category_id, db)
            product_category = product.category_id

        if product.name:
            existing_product = await ProductService.get_by_name_and_category(
                db, product.name, product_category
            )
            if existing_product and existing_product.id != db_product.id:
                raise ConflictError("Product with this name already exists in the category.")

        for key, value in product.model_dump(exclude_unset=True).items():
            setattr(db_product, key, value)

        await db.commit()
        await db.refresh(db_product)
        return db_product

    @staticmethod
    async def delete(product_id: UUID, db: AsyncSession) -> None:
        """Delete a product by its ID.

        Args:
            product_id (UUID): The ID of the product to delete.
            db (AsyncSession): The database session.
        """
        db_product = await db.get(Product, product_id)
        if not db_product:
            raise NotFoundError("Product not found.")
        await db.delete(db_product)
        await db.commit()

    @staticmethod
    async def get_by_name_and_category(
        db: AsyncSession, product_name: str, category_id: UUID
    ) -> Product | None:
        """Get a product by name and category.

        Args:
            db (AsyncSession): The database session.
            product_name (str): The name of the product.
            category_id (UUID): The ID of the category.

        Returns:
            Product | None: The product if found, otherwise None.
        """
        stmt = select(Product).where(
            (Product.name == product_name) & (Product.category_id == category_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

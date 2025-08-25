"""Service layer for product-related business logic in the ecommerce API."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_

from app.core.errors import ConflictError, NotFoundError
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.category_service import CategoryService


class ProductService:
    """Service for managing products."""

    @staticmethod
    async def list(db: AsyncSession) -> list[Product]:
        """List all products.

        Args:
            db (AsyncSession): The database session.

        Returns:
            list[Product]: A list of all products.
        """
        stmt = select(Product)
        result = await db.execute(stmt)
        return list(result.scalars().all())

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
            and_(Product.name == product_name, Product.category_id == category_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

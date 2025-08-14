"""Category service for managing categories."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.errors import ConflictError, NotFoundError
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Service for managing categories."""

    @staticmethod
    async def list(db: AsyncSession) -> list[Category]:
        """List all categories.

        Args:
            db (AsyncSession): The database session.

        Returns:
            list[Category]: A list of categories.
        """
        res = await db.execute(select(Category).order_by(Category.name))
        return list(res.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, data: CategoryCreate) -> Category:
        """Create a new category.

        Args:
            db (AsyncSession): The database session.
            data (CategoryCreate): The category data to create.

        Raises:
            ConflictError: If a category with the same name already exists.

        Returns:
            Category: The created category.
        """
        category = await CategoryService.get_by_name(db, data.name)
        if category:
            raise ConflictError("Category with this name already exists.")

        new_category = Category(**data.model_dump())
        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)
        return new_category

    @staticmethod
    async def get(db: AsyncSession, category_id: UUID) -> Category:
        """Get a category by ID.

        Args:
            db (AsyncSession): The database session.
            category_id (UUID): The ID of the category to retrieve.

        Raises:
            NotFoundError: If the category is not found.

        Returns:
            Category: The category if found, None otherwise.
        """
        category = await db.get(Category, category_id)
        if not category:
            raise NotFoundError("Category not found.")
        return category

    @staticmethod
    async def update(db: AsyncSession, category_id: UUID, data: CategoryUpdate) -> Category:
        """Update a category by ID.

        Args:
            db (AsyncSession): The database session.
            category_id (UUID): The ID of the category to update.
            data (CategoryUpdate): The updated category data.

        Raises:
            NotFoundError: If the category is not found.
            ConflictError: If a category with the same name already exists.

        Returns:
            Category: The updated category if found, None otherwise.
        """
        category = await db.get(Category, category_id)
        if not category:
            raise NotFoundError("Category not found.")

        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(category, k, v)

        existing_category = await CategoryService.get_by_name(db, category.name)
        if existing_category and existing_category.id != category.id:
            raise ConflictError("Category with this name already exists.")

        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete(db: AsyncSession, category_id: UUID) -> None:
        """Delete a category by ID.

        Args:
            db (AsyncSession): The database session.
            category_id (UUID): The ID of the category to delete.

        Returns:
            None
        """
        category = await db.get(Category, category_id)
        if category:
            await db.delete(category)
            await db.commit()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Category | None:
        """Get a category by name.

        Args:
            db (AsyncSession): The database session.
            name (str): The name of the category to retrieve.

        Returns:
            Category | None: The category if found, None otherwise.
        """
        stmt = select(Category).where(Category.name == name)
        result = await db.execute(stmt)
        return result.scalars().first()

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
    async def create(data: CategoryCreate, db: AsyncSession) -> Category:
        """Create a new category.

        Args:
            data (CategoryCreate): The category data to create.
            db (AsyncSession): The database session.

        Raises:
            ConflictError: If a category with the same name already exists.

        Returns:
            Category: The created category.
        """
        category = await CategoryService.get_by_name(data.name, db)
        if category:
            raise ConflictError("Category with this name already exists.")

        new_category = Category(**data.model_dump())
        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)
        return new_category

    @staticmethod
    async def get(category_id: UUID, db: AsyncSession) -> Category:
        """Get a category by ID.

        Args:
            category_id (UUID): The ID of the category to retrieve.
            db (AsyncSession): The database session.

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
    async def update(category_id: UUID, data: CategoryUpdate, db: AsyncSession) -> Category:
        """Update a category by ID.

        Args:
            category_id (UUID): The ID of the category to update.
            data (CategoryUpdate): The updated category data.
            db (AsyncSession): The database session.

        Raises:
            NotFoundError: If the category is not found.
            ConflictError: If a category with the same name already exists.

        Returns:
            Category: The updated category if found, None otherwise.
        """
        category = await db.get(Category, category_id)
        if not category:
            raise NotFoundError("Category not found.")

        if data.name is not None:
            existing_category = await CategoryService.get_by_name(data.name, db)
            if existing_category and existing_category.id != category.id:
                raise ConflictError("Category with this name already exists.")

        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(category, k, v)

        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete(category_id: UUID, db: AsyncSession) -> None:
        """Delete a category by ID.

        Args:
            category_id (UUID): The ID of the category to delete.
            db (AsyncSession): The database session.

        Raises:
            NotFoundError: If the category is not found.

        Returns:
            None
        """
        category = await db.get(Category, category_id)
        if category is None:
            raise NotFoundError("Category not found.")
        await db.delete(category)
        await db.commit()

    @staticmethod
    async def get_by_name(name: str, db: AsyncSession) -> Category | None:
        """Get a category by name.

        Args:
            name (str): The name of the category to retrieve.
            db (AsyncSession): The database session.

        Returns:
            Category | None: The category if found, None otherwise.
        """
        stmt = select(Category).where(Category.name == name)
        result = await db.execute(stmt)
        return result.scalars().first()

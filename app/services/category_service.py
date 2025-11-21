"""Category service for managing categories."""

from uuid import UUID

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import CategoryAlreadyExistsError, CategoryNotFoundError
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Service for managing categories."""

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
        include_inactive: bool = False,
    ) -> tuple[list[Category], int]:
        """List categories with pagination and optional search.

        Args:
            db (AsyncSession): Database session.
            limit (int): Page size.
            offset (int): Offset.
            search (str | None): Name search.
            include_inactive (bool): If True include inactive categories, otherwise only active ones.

        Returns:
            tuple[list[Category], int]: Items and total count.
        """
        stmt = select(Category)
        count_stmt = select(func.count()).select_from(Category)

        # Base filters
        if not include_inactive:
            stmt = stmt.where(Category.is_active == True)  # noqa: E712
            count_stmt = count_stmt.where(Category.is_active == True)  # noqa: E712

        stmt = stmt.order_by(Category.name).limit(limit).offset(offset)
        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(Category.name).like(pattern))
            count_stmt = count_stmt.where(func.lower(Category.name).like(pattern))

        total = (await db.exec(count_stmt)).one()
        res = await db.exec(stmt.order_by(Category.name).limit(limit).offset(offset))
        items = list(res.all())
        return items, total

    @staticmethod
    async def create(data: CategoryCreate, db: AsyncSession) -> Category:
        """Create a new category.

        Args:
            data (CategoryCreate): Category data.
            db (AsyncSession): Database session.

        Raises:
            CategoryAlreadyExistsError: If a category with the same name exists.

        Returns:
            Category: Created category.
        """
        category = await CategoryService.get_by_name(data.name, db)
        if category:
            raise CategoryAlreadyExistsError()

        new_category = Category(**data.model_dump())
        db.add(new_category)
        await db.flush()
        await db.refresh(new_category)
        return new_category

    @staticmethod
    async def get(category_id: UUID, db: AsyncSession) -> Category:
        """Get a category by ID.

        Args:
            category_id (UUID): Category ID.
            db (AsyncSession): Database session.

        Raises:
            CategoryNotFoundError: If the category does not exist.

        Returns:
            Category: Retrieved category.
        """
        category = await db.get(Category, category_id)
        if not category:
            raise CategoryNotFoundError()
        return category

    @staticmethod
    async def update(category_id: UUID, data: CategoryUpdate, db: AsyncSession) -> Category:
        """Update a category.

        Args:
            category_id (UUID): Category ID.
            data (CategoryUpdate): Update data.
            db (AsyncSession): Database session.

        Raises:
            CategoryNotFoundError: If the category does not exist.
            CategoryAlreadyExistsError: If new name duplicates another category.

        Returns:
            Category: Updated category.
        """
        category = await db.get(Category, category_id)
        if not category:
            raise CategoryNotFoundError()

        if data.name is not None:
            existing_category = await CategoryService.get_by_name(data.name, db)
            if existing_category and existing_category.id != category.id:
                raise CategoryAlreadyExistsError()

        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(category, k, v)

        await db.flush()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete(category_id: UUID, db: AsyncSession) -> None:
        """Delete a category.

        Args:
            category_id (UUID): Category ID.
            db (AsyncSession): Database session.

        Raises:
            CategoryNotFoundError: If the category does not exist.
        """
        category = await db.get(Category, category_id)
        if category is None:
            raise CategoryNotFoundError()
        await db.delete(category)
        await db.flush()

    @staticmethod
    async def get_by_name(name: str, db: AsyncSession) -> Category | None:
        """Get a category by name.

        Args:
            name (str): Category name.
            db (AsyncSession): Database session.

        Returns:
            Category | None: Matching category or None.
        """
        stmt = select(Category).where(Category.name == name)
        result = await db.exec(stmt)
        return result.first()

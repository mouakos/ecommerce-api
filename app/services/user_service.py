"""Service for managing users outside authentication concerns."""

from __future__ import annotations

from uuid import UUID

from sqlmodel import desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.enums import UserRole
from app.core.errors import UserNotFoundError
from app.models.user import User
from app.schemas.user import UserUpdate


class UserService:
    """Business logic for user retrieval and profile maintenance."""

    @staticmethod
    async def get(db: AsyncSession, user_id: UUID) -> User:
        """Fetch a user by id.

        Args:
            db (AsyncSession): Database session.
            user_id (UUID): User ID.

        Raises:
            UserNotFoundError: If the user does not exist.
        """
        user = await db.get(User, user_id)
        if not user:
            raise UserNotFoundError()
        return user

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """Fetch a user by email or return None.

        Args:
            db (AsyncSession): Database session.
            email (str): User email.

        Returns:
            User | None: The user or None if not found.
        """
        stmt = select(User).where(User.email == email)
        res = await db.exec(stmt)
        return res.first()

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        """Paginated listing of users, optional case-insensitive search on email.

        Args:
            db (AsyncSession): Database session.
            limit (int): Maximum number of users to return.
            offset (int): Number of users to skip.
            search (str | None): Optional case-insensitive search string for email.

        Returns:
            tuple[list[User], int]: List of users and total count.
        """
        base_stmt = select(User).order_by(desc(User.created_at))
        count_stmt = select(func.count()).select_from(User)
        if search:
            pattern = f"%{search.lower()}%"
            base_stmt = base_stmt.where(func.lower(User.email).like(pattern))
            count_stmt = count_stmt.where(func.lower(User.email).like(pattern))
        total = (await db.exec(count_stmt)).one()
        res = await db.exec(base_stmt.limit(limit).offset(offset))
        return list(res.all()), total

    @staticmethod
    async def update_profile(db: AsyncSession, user_id: UUID, data: UserUpdate) -> User:
        """Update mutable profile fields (first/last name, phone number).

        Args:
            db (AsyncSession): Database session.
            user_id (UUID): User ID.
            data (UserUpdate): Data to update.

        Raises:
            UserNotFoundError: If the user does not exist.
        """
        user = await UserService.get(db, user_id)
        payload = data.model_dump(exclude_unset=True)
        for key, value in payload.items():
            if value is None:
                continue
            setattr(user, key, value)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def deactivate(db: AsyncSession, user_id: UUID) -> None:
        """Soft-deactivate a user account (is_active=False).

        Args:
            db (AsyncSession): Database session.
            user_id (UUID): User ID.

        Raises:
                UserNotFoundError: If the user does not exist.
        """
        user = await UserService.get(db, user_id)
        user.is_active = False
        db.add(user)
        await db.flush()

    @staticmethod
    async def activate(db: AsyncSession, user_id: UUID) -> None:
        """Re-activate a user account (is_active=True).

        Args:
            db (AsyncSession): Database session.
            user_id (UUID): User ID.

        Raises:
            UserNotFoundError: If the user does not exist.
        """
        user = await UserService.get(db, user_id)
        user.is_active = True
        db.add(user)
        await db.flush()

    @staticmethod
    async def set_role(db: AsyncSession, user_id: UUID, role: UserRole) -> None:
        """Assign a new role to a user (e.g. 'admin', 'user').

        Args:
            db (AsyncSession): Database session.
            user_id (UUID): User ID.
            role (UserRole): New role to assign.

        Raises:
            UserNotFoundError: If the user does not exist.
        """
        user = await UserService.get(db, user_id)
        user.role = role
        db.add(user)
        await db.flush()

    @staticmethod
    async def delete(db: AsyncSession, user_id: UUID) -> None:
        """Delete a user permanently.

        Args:
            db (AsyncSession): Database session.
            user_id (UUID): User ID.

        Raises:
            UserNotFoundError: If the user does not exist.
        """
        user = await UserService.get(db, user_id)
        await db.delete(user)
        await db.flush()

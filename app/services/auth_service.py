"""Service for managing user authentication."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.errors import BadRequestError, ConflictError
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


class AuthService:
    """Service for managing user authentication."""

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        """Get a user by email.

        Args:
            db (AsyncSession): Database session.
            email (str): User email.

        Returns:
            User | None: The user or None if not found.
        """
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, data: UserCreate) -> User:
        """Create a new user.

        Raises:
            ConflictError: If the email is already registered.

        Returns:
            User: The created user.
        """
        existing_user = await AuthService.get_user_by_email(db, data.email)
        if existing_user:
            raise ConflictError("Email already registered.")

        user = User(email=data.email, hashed_password=get_password_hash(data.password))

        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
        """Authenticate a user.

        Args:
            db (AsyncSession): Database session.
            email (str): User email.
            password (str): User password.

        Raises:
            BadRequestError: If the email or password is invalid.

        Returns:
            User: The authenticated user.
        """
        user = await AuthService.get_user_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise BadRequestError("Invalid email or password.")
        return user

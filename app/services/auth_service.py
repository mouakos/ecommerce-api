"""Service for managing user authentication (credentials & password flows only).

Email / profile / listing concerns live in ``UserService``.
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import (
    InvalidCredentialsError,
    PasswordMismatchError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import UserService


class AuthService:
    """Authentication-centric operations: create account, authenticate, verify email, change password."""

    @staticmethod
    async def create_user(db: AsyncSession, data: UserCreate) -> User:
        """Create a new user.

        Raises:
            UserAlreadyExistsError: If the email is already registered.

        Returns:
            User: The created user.
        """
        existing_user = await UserService.get_by_email(db, data.email)
        if existing_user:
            raise UserAlreadyExistsError()

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
        user = await UserService.get_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        return user

    @staticmethod
    async def verify_user_email(db: AsyncSession, email: str) -> None:
        """Verify a user's email.

        Args:
            db (AsyncSession): Database session.
            email (str): User email.

        Raises:
            UserNotFoundError: If the user does not exist.
        """
        user = await UserService.get_by_email(db, email)
        if not user:
            raise UserNotFoundError()
        user.is_verified = True
        db.add(user)
        await db.flush()
        await db.commit()

    @staticmethod
    async def change_user_password(
        db: AsyncSession, user_email: str, new_password: str, confirm_new_password: str
    ) -> None:
        """Change a user's password.

        Args:
            db (AsyncSession): Database session.
            user_email (str): The email of the user whose password is to be changed.
            new_password (str): The new password.
            confirm_new_password (str): Confirmation of the new password.

        Raises:
            UserNotFoundError: If the user does not exist.
            PasswordMismatchError: If the new password and confirmation do not match.
        """
        user = await UserService.get_by_email(db, user_email)
        if not user:
            raise UserNotFoundError()

        if new_password != confirm_new_password:
            raise PasswordMismatchError()

        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        await db.flush()
        await db.commit()

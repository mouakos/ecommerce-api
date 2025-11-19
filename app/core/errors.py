"""Error definitions for the application."""


class EcomError(Exception):
    """This is the base class for all ecom errors."""

    pass


class InvalidTokenError(EcomError):
    """User has provided an invalid or expired token."""

    pass


class RevokedTokenError(EcomError):
    """User has provided a token that has been revoked."""

    pass


class AccessTokenRequiredError(EcomError):
    """User has provided a refresh token when an access token is needed."""

    pass


class RefreshTokenRequiredError(EcomError):
    """User has provided an access token when a refresh token is needed."""

    pass


class UserAlreadyExistsError(EcomError):
    """User has provided an email for a user who exists during sign up."""

    pass


class InvalidCredentialsError(EcomError):
    """User has provided wrong email or password during log in."""

    pass


class InsufficientPermissionError(EcomError):
    """User does not have the necessary permissions to perform an action."""

    pass


class UserNotFoundError(EcomError):
    """User Not found."""

    pass


class ProductNotFoundError(EcomError):
    """Product Not found."""

    pass


class ProductAlreadyExistsError(EcomError):
    """Product already exists."""

    pass


class CategoryNotFoundError(EcomError):
    """Category Not found."""

    pass


class CategoryAlreadyExistsError(EcomError):
    """Category already exists."""

    pass


class OrderNotFoundError(EcomError):
    """Order Not found."""

    pass


class InsufficientStockError(EcomError):
    """Not enough stock for the requested product."""

    pass


class EmptyCartError(EcomError):
    """The cart is empty when trying to create an order."""

    pass


class CartItemNotFoundError(EcomError):
    """Cart item not found."""

    pass


class ReviewNotFoundError(EcomError):
    """Review not found."""

    pass


class UserReviewProductAlreadyExistsError(EcomError):
    """User has already reviewed this product."""

    pass


class UserEmailVerificationError(EcomError):
    """User email could not be verified."""

    pass


class AccountNotVerifiedError(EcomError):
    """User account is not verified."""

    pass


class EmailSendingError(EcomError):
    """Error occurred while sending an email."""

    pass

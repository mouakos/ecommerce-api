"""Error Handler."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.errors import (
    AccessTokenRequiredError,
    CartItemNotFoundError,
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
    EcomError,
    EmptyCartError,
    InsufficientPermissionError,
    InsufficientStockError,
    InvalidCredentialsError,
    InvalidTokenError,
    OrderNotFoundError,
    ProductAlreadyExistsError,
    ProductNotFoundError,
    RefreshTokenRequiredError,
    ReviewNotFoundError,
    RevokedTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserReviewProductAlreadyExistsError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(InvalidTokenError)
    async def handle_invalid_token_error(_: Request, _exc: InvalidTokenError) -> JSONResponse:
        """Handle not found errors."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Token is invalid or expired.",
                "solution": "Please get new token.",
                "error_code": "invalid_token",
            },
        )

    @app.exception_handler(RevokedTokenError)
    async def handle_revoked_token_error(_: Request, _exc: RevokedTokenError) -> JSONResponse:
        """Handle revoked token errors."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Token is invalid or has been revoked.",
                "solution": "Please get new token.",
                "error_code": "token_revoked",
            },
        )

    @app.exception_handler(RefreshTokenRequiredError)
    async def handle_refresh_token_required_error(
        _: Request, _exc: RefreshTokenRequiredError
    ) -> JSONResponse:
        """Handle refresh token required errors."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Please provide a valid refresh token.",
                "solution": "Please get a refresh token.",
                "error_code": "refresh_token_required",
            },
        )

    @app.exception_handler(AccessTokenRequiredError)
    async def handle_access_token_required_error(
        _: Request, _exc: AccessTokenRequiredError
    ) -> JSONResponse:
        """Handle access token required errors."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Please provide a valid access token.",
                "solution": "Please get an access token.",
                "error_code": "access_token_required",
            },
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def handle_user_already_exists_error(
        _: Request, _exc: UserAlreadyExistsError
    ) -> JSONResponse:
        """Handle user already exists errors."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "User with email already exists.",
                "error_code": "user_already_exists",
            },
        )

    @app.exception_handler(InvalidCredentialsError)
    async def handle_invalid_credentials_error(
        _: Request, _exc: InvalidCredentialsError
    ) -> JSONResponse:
        """Handle invalid credentials errors."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Invalid Email or Password.",
                "error_code": "invalid_email_or_password",
            },
        )

    @app.exception_handler(InsufficientPermissionError)
    async def handle_insufficient_permission_error(
        _: Request, _exc: InsufficientPermissionError
    ) -> JSONResponse:
        """Handle insufficient permission errors."""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": "You do not have enough permissions to perform this action.",
                "error_code": "insufficient_permissions",
            },
        )

    @app.exception_handler(UserNotFoundError)
    async def handle_user_not_found_error(_: Request, _exc: UserNotFoundError) -> JSONResponse:
        """Handle user not found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "User not found.", "error_code": "user_not_found"},
        )

    @app.exception_handler(ProductNotFoundError)
    async def handle_product_not_found_error(
        _: Request, _exc: ProductNotFoundError
    ) -> JSONResponse:
        """Handle product not found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Product not found.", "error_code": "product_not_found"},
        )

    @app.exception_handler(ProductAlreadyExistsError)
    async def handle_product_already_exists_error(
        _: Request, _exc: ProductAlreadyExistsError
    ) -> JSONResponse:
        """Handle product already exists errors."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Product already exists.",
                "error_code": "product_already_exists",
            },
        )

    @app.exception_handler(CategoryNotFoundError)
    async def handle_category_not_found_error(
        _: Request, _exc: CategoryNotFoundError
    ) -> JSONResponse:
        """Handle category not found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Category not found.", "error_code": "category_not_found"},
        )

    @app.exception_handler(CategoryAlreadyExistsError)
    async def handle_category_already_exists_error(
        _: Request, _exc: CategoryAlreadyExistsError
    ) -> JSONResponse:
        """Handle category already exists errors."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Category already exists.",
                "error_code": "category_already_exists",
            },
        )

    @app.exception_handler(OrderNotFoundError)
    async def handle_order_not_found_error(_: Request, _exc: OrderNotFoundError) -> JSONResponse:
        """Handle order not found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Order not found.", "error_code": "order_not_found"},
        )

    @app.exception_handler(InsufficientStockError)
    async def handle_insufficient_stock_error(
        _: Request, _exc: InsufficientStockError
    ) -> JSONResponse:
        """Handle insufficient stock errors."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Insufficient stock.", "error_code": "insufficient_stock"},
        )

    @app.exception_handler(EmptyCartError)
    async def handle_empty_cart_error(_: Request, _exc: EmptyCartError) -> JSONResponse:
        """Handle empty cart errors."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Cart is empty.", "error_code": "empty_cart"},
        )

    @app.exception_handler(CartItemNotFoundError)
    async def handle_cart_item_not_found_error(
        _: Request, _exc: CartItemNotFoundError
    ) -> JSONResponse:
        """Handle cart item not found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Cart item not found.", "error_code": "cart_item_not_found"},
        )

    @app.exception_handler(ReviewNotFoundError)
    async def handle_review_not_found_error(_: Request, _exc: ReviewNotFoundError) -> JSONResponse:
        """Handle review not found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Review not found.", "error_code": "review_not_found"},
        )

    @app.exception_handler(UserReviewProductAlreadyExistsError)
    async def handle_user_review_product_already_exists_error(
        _: Request, _exc: UserReviewProductAlreadyExistsError
    ) -> JSONResponse:
        """Handle user review product already exists errors."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "User has already reviewed this product.",
                "error_code": "user_review_product_already_exists",
            },
        )

    @app.exception_handler(EcomError)
    async def handle_unhandled_ecom_error(_: Request, _exc: EcomError) -> JSONResponse:
        """Catch-all for unmapped EcomError subclasses.

        Returns 400 to indicate a client-side domain issue when a specific mapping
        wasn't provided. If the exception has a message, include it; otherwise use a generic detail.
        """
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": str(_exc) or "Unhandled application error.",
                "error_code": "unhandled_ecom_error",
            },
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(_: Request, _exc: Exception) -> JSONResponse:  # noqa: BLE001
        """Generic fallback for any uncaught exception.

        We do not expose internal details for security reasons.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error.",
                "error_code": "internal_server_error",
            },
        )

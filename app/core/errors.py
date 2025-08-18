"""Error definitions for the application."""


class AppError(Exception):
    """Base app error."""


class NotFoundError(AppError):
    """Resource not found error."""

    pass


class ConflictError(AppError):
    """Conflict error."""

    pass


class BadRequestError(AppError):
    """Bad request error."""

    pass


class UnauthorizedError(AppError):
    """Unauthorized error."""

    pass

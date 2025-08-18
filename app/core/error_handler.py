"""Error Handler."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import BadRequestError, ConflictError, NotFoundError, UnauthorizedError


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(NotFoundError)
    async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        """Handle not found errors."""
        return JSONResponse(status_code=404, content={"detail": str(exc) or "Not found"})

    @app.exception_handler(ConflictError)
    async def handle_conflict(_: Request, exc: ConflictError) -> JSONResponse:
        """Handle conflict errors."""
        return JSONResponse(status_code=409, content={"detail": str(exc) or "Conflict"})

    @app.exception_handler(BadRequestError)
    async def handle_bad_request(_: Request, exc: BadRequestError) -> JSONResponse:
        """Handle bad request errors."""
        return JSONResponse(status_code=400, content={"detail": str(exc) or "Bad request"})

    @app.exception_handler(UnauthorizedError)
    async def handle_unauthorized(_: Request, exc: UnauthorizedError) -> JSONResponse:
        """Handle unauthorized errors."""
        return JSONResponse(status_code=401, content={"detail": str(exc) or "Unauthorized"})

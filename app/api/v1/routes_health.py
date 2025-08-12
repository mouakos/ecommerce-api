"""Health check routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

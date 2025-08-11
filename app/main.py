"""Main application entry point."""

from fastapi import FastAPI

from app.api.v1.routes_health import router as health_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)

app.include_router(health_router, prefix="/api/v1")

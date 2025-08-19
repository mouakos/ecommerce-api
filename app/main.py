"""Main application entry point."""

from fastapi import FastAPI

from app.api.v1.auth_routes import router as auth_router
from app.api.v1.cart_routes import router as cart_router
from app.api.v1.category_routes import router as category_router
from app.api.v1.product_routes import router as product_router
from app.core.error_handler import register_exception_handlers

app = FastAPI(
    description="This is a simple e-commerce API built with FastAPI.",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    title="E-commerce API",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/license/mit/",
    },
    version="v1",
    contact={
        "name": "Stephane Mouako",
        "url": "https://github.com/mouakos",
    },
    swagger_ui_parameters={
        "syntaxHighlight.theme": "monokai",
        "layout": "BaseLayout",
        "filter": True,
        "tryItOutEnabled": True,
        "onComplete": "Ok",
    },
)


# Register handlers
register_exception_handlers(app)


# Include routers
app.include_router(auth_router)
app.include_router(cart_router)
app.include_router(category_router)
app.include_router(product_router)

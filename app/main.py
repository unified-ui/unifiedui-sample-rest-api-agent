"""FastAPI application factory."""

from fastapi import FastAPI

from app.api.v1.agent import router as agent_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.health import router as health_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="unified-ui Sample REST API Agent",
        description="Sample REST API agent service demonstrating unified-ui SDK integration",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.include_router(health_router)
    application.include_router(conversations_router)
    application.include_router(agent_router)

    return application


app = create_app()

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get(
    "/health",
    tags=["System"],
    summary="Health check endpoint",
    description="Simple endpoint to verify API is running. Useful for Kubernetes/Docker health probes.",
)
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns basic status information about the API.
    Useful for monitoring and health probes in containerized environments.
    """
    try:
        provider = settings.get_llm_provider()
        model = settings.DEFAULT_MODEL
    except ValueError:
        provider = "not_configured"
        model = "not_configured"

    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "llm_provider": provider,
        "default_model": model,
    }


@router.get(
    "/",
    tags=["System"],
    summary="Root endpoint",
    description="Returns API information and available endpoints.",
)
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "AI Slide Deck Generation Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }

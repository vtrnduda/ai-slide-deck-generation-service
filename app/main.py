import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import system
from app.api.v1 import endpoints as v1_endpoints
from app.core.config import settings

app = FastAPI(
    title="AI Slide Deck Generation Service",
    description=(
        "Backend service for generating educational slide decks using GenAI. "
        "Supports OpenAI and Google Gemini models via LangChain. "
        "Generates structured presentations with title, agenda, content, and conclusion slides."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


def get_cors_origins() -> list[str]:
    """
    Get CORS allowed origins from settings or use defaults.

    Returns:
        List of allowed origin URLs.
    """
    return [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register routers
app.include_router(system.router)
app.include_router(v1_endpoints.router, prefix="/api/v1", tags=["Presentations"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )

"""API v1 routes."""

from fastapi import APIRouter
from app.api.v1.routes import chat, vision, embeddings, models, health

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(vision.router, prefix="/vision", tags=["Vision"])
api_router.include_router(embeddings.router, prefix="/embeddings", tags=["Embeddings"])
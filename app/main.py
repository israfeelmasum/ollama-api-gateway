"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.v1 import api_router
from app.middleware.logging import LoggingMiddleware
from app.middleware.auth import AuthMiddleware
from app.services.ollama_proxy import ollama_proxy
from app import __version__, __author__

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("ollama_gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Handles startup and shutdown procedures.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Starting Ollama API Gateway v%s", __version__)
    logger.info("=" * 60)
    logger.info("📍 Ollama URL: %s", settings.ollama_base_url)
    logger.info("🔐 Auth Required: %s", settings.require_api_key)
    logger.info("🌐 CORS Origins: %s", settings.cors_origins)
    logger.info("🔧 Debug Mode: %s", settings.debug)
    logger.info("=" * 60)

    # Check Ollama connectivity
    try:
        is_healthy = await ollama_proxy.health_check()
        if is_healthy:
            logger.info("✅ Ollama connection successful")
        else:
            logger.warning("⚠️  Ollama connection failed - service may not work correctly")
    except Exception as e:
        logger.error("❌ Ollama health check error: %s", str(e))

    yield

    # Shutdown
    logger.info("=" * 60)
    logger.info("👋 Shutting down Ollama API Gateway...")
    logger.info("=" * 60)
    await ollama_proxy.close()
    logger.info("✅ Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title="Ollama API Gateway",
    description=(
        "A stateless API gateway for Ollama with intelligent model type detection "
        "and OpenAI-compatible endpoints. Provides secure access to local LLMs "
        "with zero data persistence."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": __author__,
        "url": "https://github.com/yourusername/ollama-api-gateway",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add custom logging middleware
app.add_middleware(LoggingMiddleware)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Include API v1 routes
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing basic API information.

    Returns links to documentation and health check.
    """
    return {
        "name": "Ollama API Gateway",
        "version": __version__,
        "description": "Stateless proxy for Ollama with model type detection",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health",
        "api_version": "v1",
        "endpoints": {
            "chat": "/api/v1/chat",
            "vision": "/api/v1/vision",
            "embeddings": "/api/v1/embeddings",
            "models": "/api/v1/models"
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions gracefully."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# Run with uvicorn if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
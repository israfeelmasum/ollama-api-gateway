"""Health check endpoints."""

from fastapi import APIRouter, HTTPException
from app.services.ollama_proxy import ollama_proxy
from app.config import settings
from app import __version__

router = APIRouter()


@router.get("")
async def health_check():
    """
    Check API gateway health and Ollama connectivity.

    Returns basic health status without requiring authentication.
    """
    is_healthy = await ollama_proxy.health_check()

    return {
        "status": "healthy" if is_healthy else "degraded",
        "ollama_reachable": is_healthy,
        "gateway_version": __version__,
        "ollama_url": settings.ollama_base_url
    }


@router.get("/status")
async def detailed_status():
    """
    Get detailed system status including model information.

    Requires authentication.
    """
    try:
        # Check Ollama health
        is_healthy = await ollama_proxy.health_check()

        if not is_healthy:
            raise HTTPException(status_code=503, detail="Ollama service unavailable")

        # Get models
        models_data = await ollama_proxy.list_models()
        models_list = models_data.get("models", [])

        # Get running models
        try:
            running_data = await ollama_proxy.running_models()
            running_list = running_data.get("models", [])
        except Exception:
            running_list = []

        # Count by type
        from app.services.model_classifier import model_classifier
        type_counts = {}
        for model in models_list:
            info = model_classifier.classify_model(model.get("name", ""))
            model_type = info["type"]
            type_counts[model_type] = type_counts.get(model_type, 0) + 1

        return {
            "ollama_connected": True,
            "models_available": len(models_list),
            "models_loaded": len(running_list),
            "running_models": [
                {
                    "name": m.get("name"),
                    "size_vram": m.get("size_vram", 0)
                }
                for m in running_list
            ],
            "model_types": type_counts,
            "gateway_version": __version__
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
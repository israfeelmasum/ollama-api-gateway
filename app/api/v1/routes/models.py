"""Model management endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.ollama_proxy import ollama_proxy
from app.services.model_classifier import model_classifier
from app.core.model_types import ModelType

router = APIRouter()


@router.get("")
async def list_models(
        type: Optional[str] = Query(None, description="Filter by model type")
):
    """
    List all available models with type detection.

    Optionally filter by model type (text, vision, embedding, code).
    """
    try:
        # Get models from Ollama
        data = await ollama_proxy.list_models()
        models_list = data.get("models", [])

        # Enrich with type information
        enriched_models = []
        for model in models_list:
            enriched = model_classifier.enrich_model_info(model)

            # Filter by type if specified
            if type and enriched.get("type") != type:
                continue

            enriched_models.append(enriched)

        return {
            "models": enriched_models,
            "total": len(enriched_models)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/catalog")
async def get_model_catalog():
    """
    Get full model catalog organized by type.

    Returns models grouped by their detected type.
    """
    try:
        data = await ollama_proxy.list_models()
        models_list = data.get("models", [])

        # Organize by type
        catalog = {
            "text": [],
            "vision": [],
            "embedding": [],
            "code": []
        }

        for model in models_list:
            enriched = model_classifier.enrich_model_info(model)
            model_type = enriched.get("type", "text")
            if model_type in catalog:
                catalog[model_type].append(enriched)

        return {
            "model_types": catalog,
            "total_models": len(models_list)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get catalog: {str(e)}")


@router.get("/{model_name}/info")
async def get_model_info(model_name: str):
    """
    Get detailed information about a specific model.

    Includes type detection and recommended endpoints.
    """
    try:
        # Get model details from Ollama
        data = await ollama_proxy.show_model(model_name)

        # Classify model
        classification = model_classifier.classify_model(model_name)
        model_type = ModelType(classification["type"])

        # Get recommended endpoints
        recommended_endpoints = model_classifier.get_recommended_endpoints(model_type)

        return {
            **data,
            "type": classification["type"],
            "capabilities": classification["capabilities"],
            "family": classification["family"],
            "recommended_endpoints": recommended_endpoints
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model not found: {str(e)}")


@router.post("/classify")
async def classify_model_endpoint(model_name: str):
    """
    Classify a model by name without querying Ollama.

    Useful for checking what type a model would be detected as.
    """
    try:
        classification = model_classifier.classify_model(model_name)
        model_type = ModelType(classification["type"])

        return {
            "model": model_name,
            "detected_type": classification["type"],
            "confidence": "high" if classification["detection_method"] == "pattern_matching" else "medium",
            "capabilities": classification["capabilities"],
            "family": classification["family"],
            "recommended_endpoints": model_classifier.get_recommended_endpoints(model_type)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
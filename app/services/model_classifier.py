"""Model classification and type detection service."""

from typing import Dict, Any, Optional
from app.core.model_types import (
    ModelType,
    ModelCapability,
    detect_model_type,
    get_model_capabilities,
    get_model_family
)


class ModelClassifier:
    """Service for classifying and enriching model information."""

    @staticmethod
    def classify_model(model_name: str) -> Dict[str, Any]:
        """
        Classify a model and return enriched information.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with model classification details
        """
        model_type = detect_model_type(model_name)
        capabilities = get_model_capabilities(model_name, model_type)
        family = get_model_family(model_name)

        return {
            "name": model_name,
            "type": model_type.value,
            "capabilities": [cap.value for cap in capabilities],
            "family": family,
            "detection_method": "pattern_matching"
        }

    @staticmethod
    def get_recommended_endpoints(model_type: ModelType) -> list[str]:
        """
        Get recommended API endpoints for a model type.

        Args:
            model_type: Type of the model

        Returns:
            List of endpoint paths
        """
        endpoint_map = {
            ModelType.TEXT: [
                "POST /api/v1/chat/completions",
                "POST /api/v1/chat/stream"
            ],
            ModelType.VISION: [
                "POST /api/v1/vision/chat",
                "POST /api/v1/chat/completions"
            ],
            ModelType.EMBEDDING: [
                "POST /api/v1/embeddings",
                "POST /api/v1/embeddings/batch"
            ],
            ModelType.CODE: [
                "POST /api/v1/chat/completions",
                "POST /api/v1/chat/stream"
            ]
        }
        return endpoint_map.get(model_type, ["POST /api/v1/chat/completions"])

    @staticmethod
    def enrich_model_info(model_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich model information with type detection.

        Args:
            model_info: Raw model info from Ollama

        Returns:
            Enriched model information
        """
        model_name = model_info.get("name", "")
        classification = ModelClassifier.classify_model(model_name)

        # Add classification to model info
        model_info.update({
            "type": classification["type"],
            "capabilities": classification["capabilities"],
            "family": classification["family"]
        })

        # Format size if present
        if "size" in model_info and isinstance(model_info["size"], int):
            size_bytes = model_info["size"]
            if size_bytes >= 1_000_000_000:
                model_info["size_formatted"] = f"{size_bytes / 1_000_000_000:.1f}GB"
            else:
                model_info["size_formatted"] = f"{size_bytes / 1_000_000:.0f}MB"

        return model_info


# Global instance
model_classifier = ModelClassifier()
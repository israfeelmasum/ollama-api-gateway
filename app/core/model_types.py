"""Model type definitions and classification patterns."""

from typing import Dict, List, Optional
from enum import Enum


class ModelType(str, Enum):
    """Supported model types."""
    TEXT = "text"
    VISION = "vision"
    EMBEDDING = "embedding"
    CODE = "code"
    UNKNOWN = "unknown"


class ModelCapability(str, Enum):
    """Model capabilities."""
    CHAT = "chat"
    COMPLETION = "completion"
    VISION = "vision"
    EMBEDDING = "embedding"
    CODE = "code"
    STREAMING = "streaming"


# Model name patterns for type detection
MODEL_PATTERNS: Dict[ModelType, List[str]] = {
    ModelType.VISION: ["llava", "bakllava", "vision", "moondream"],
    ModelType.EMBEDDING: ["embed", "nomic", "minilm", "bge", "e5", "gte"],
    ModelType.CODE: ["code", "codellama", "starcoder", "deepseek-coder", "wizardcoder"],
}

# Known model configurations
KNOWN_MODELS: Dict[str, Dict] = {
    "nomic-embed-text": {
        "type": ModelType.EMBEDDING,
        "dimensions": 768,
        "context_length": 8192,
        "capabilities": [ModelCapability.EMBEDDING]
    },
    "llava": {
        "type": ModelType.VISION,
        "max_images": 10,
        "capabilities": [ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.STREAMING]
    },
    "bakllava": {
        "type": ModelType.VISION,
        "max_images": 10,
        "capabilities": [ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.STREAMING]
    },
    "codellama": {
        "type": ModelType.CODE,
        "capabilities": [ModelCapability.CHAT, ModelCapability.CODE, ModelCapability.STREAMING]
    },
}

# Model family patterns
MODEL_FAMILIES: Dict[str, str] = {
    "llama": "llama",
    "mistral": "mistral",
    "phi": "phi",
    "gemma": "gemma",
    "qwen": "qwen",
    "llava": "llava",
    "deepseek": "deepseek",
}


def detect_model_type(model_name: str) -> ModelType:
    """
    Detect model type from model name.

    Args:
        model_name: Name of the model (e.g., "llama3.2", "llava:13b")

    Returns:
        Detected ModelType
    """
    model_lower = model_name.lower()

    # Check known models first (exact match without version)
    base_name = model_lower.split(":")[0]
    if base_name in KNOWN_MODELS:
        return KNOWN_MODELS[base_name]["type"]

    # Check patterns
    for model_type, patterns in MODEL_PATTERNS.items():
        if any(pattern in model_lower for pattern in patterns):
            return model_type

    # Default to text
    return ModelType.TEXT


def get_model_capabilities(model_name: str, model_type: Optional[ModelType] = None) -> List[ModelCapability]:
    """
    Get capabilities for a model.

    Args:
        model_name: Name of the model
        model_type: Optional pre-detected model type

    Returns:
        List of capabilities
    """
    base_name = model_name.lower().split(":")[0]

    # Check known models
    if base_name in KNOWN_MODELS:
        return KNOWN_MODELS[base_name].get("capabilities", [])

    # Infer from type
    if not model_type:
        model_type = detect_model_type(model_name)

    capabilities = [ModelCapability.STREAMING]  # Most models support streaming

    if model_type == ModelType.TEXT:
        capabilities.extend([ModelCapability.CHAT, ModelCapability.COMPLETION])
    elif model_type == ModelType.VISION:
        capabilities.extend([ModelCapability.CHAT, ModelCapability.VISION])
    elif model_type == ModelType.EMBEDDING:
        capabilities = [ModelCapability.EMBEDDING]
    elif model_type == ModelType.CODE:
        capabilities.extend([ModelCapability.CHAT, ModelCapability.CODE, ModelCapability.COMPLETION])

    return capabilities


def get_model_family(model_name: str) -> Optional[str]:
    """
    Extract model family from name.

    Args:
        model_name: Name of the model

    Returns:
        Model family name or None
    """
    model_lower = model_name.lower()

    for pattern, family in MODEL_FAMILIES.items():
        if pattern in model_lower:
            return family

    return None
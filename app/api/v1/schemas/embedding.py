"""Embedding endpoint schemas."""

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """Single embedding request."""
    model: str = Field(..., description="Embedding model name (e.g. nomic-embed-text)")
    input: Optional[Union[str, List[str]]] = Field(None, description="Text or list of texts to embed")
    prompt: Optional[str] = Field(None, description="(Deprecated) Use 'input' instead")


class EmbeddingBatchRequest(BaseModel):
    """Batch embedding request."""
    model: str = Field(..., description="Embedding model name")
    inputs: List[str] = Field(..., description="List of texts to embed")


class EmbeddingResponse(BaseModel):
    """Embedding response from Ollama /api/embed."""
    model: str
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")


class EmbeddingBatchResponse(BaseModel):
    """Batch embedding response."""
    model: str
    embeddings: List[dict]

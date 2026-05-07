"""Embedding generation endpoints."""

from fastapi import APIRouter, HTTPException
from app.api.v1.schemas.embedding import (
    EmbeddingRequest,
    EmbeddingBatchRequest,
    EmbeddingResponse,
    EmbeddingBatchResponse
)
from app.services.ollama_proxy import ollama_proxy

router = APIRouter()


@router.post("", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """
    Generate embedding for text input.

    Uses Ollama's /api/embed endpoint. Accepts a single string or list of strings.
    """
    try:
        # Support both 'input' and legacy 'prompt' field
        text_input = request.input if request.input else request.prompt
        if not text_input:
            raise HTTPException(status_code=400, detail="Either 'input' or 'prompt' must be provided")

        payload = {
            "model": request.model,
            "input": text_input
        }

        response = await ollama_proxy.embeddings(payload)

        return {
            "model": request.model,
            "embeddings": response.get("embeddings", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@router.post("/batch", response_model=EmbeddingBatchResponse)
async def generate_embeddings_batch(request: EmbeddingBatchRequest):
    """
    Generate embeddings for multiple texts (batch processing).

    Sends all inputs in a single call to Ollama's /api/embed endpoint.
    """
    try:
        payload = {
            "model": request.model,
            "input": request.inputs
        }

        response = await ollama_proxy.embeddings(payload)

        raw_embeddings = response.get("embeddings", [])
        embeddings = []
        for idx, text in enumerate(request.inputs):
            embedding = raw_embeddings[idx] if idx < len(raw_embeddings) else []
            embeddings.append({
                "index": idx,
                "text": text,
                "embedding": embedding
            })

        return {
            "model": request.model,
            "embeddings": embeddings
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch embedding failed: {str(e)}")

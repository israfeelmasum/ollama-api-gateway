"""Chat completion endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.api.v1.schemas.chat import ChatCompletionRequest
from app.services.ollama_proxy import ollama_proxy
from app.core.security import verify_api_key

router = APIRouter()


@router.post("/completions", dependencies=[Depends(verify_api_key)])
async def chat_completion(request: ChatCompletionRequest):
    """
    Create a chat completion (non-streaming).

    Supports OpenAI-compatible message format.
    Requires valid API key.
    """
    try:
        # Prepare Ollama payload
        payload = {
            "model": request.model,
            "messages": [msg.model_dump() for msg in request.messages],
            "stream": False
        }

        # Add optional parameters
        options = {}
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens
        if request.top_p is not None:
            options["top_p"] = request.top_p
        if request.top_k is not None:
            options["top_k"] = request.top_k

        if options:
            payload["options"] = options

        # Call Ollama
        response = await ollama_proxy.chat(payload)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@router.post("/stream", dependencies=[Depends(verify_api_key)])
async def chat_stream(request: ChatCompletionRequest):
    """
    Create a streaming chat completion.

    Returns Server-Sent Events (SSE) stream.
    Requires valid API key.
    """
    try:
        # Prepare Ollama payload
        payload = {
            "model": request.model,
            "messages": [msg.model_dump() for msg in request.messages],
            "stream": True
        }

        # Add optional parameters
        options = {}
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens
        if request.top_p is not None:
            options["top_p"] = request.top_p
        if request.top_k is not None:
            options["top_k"] = request.top_k

        if options:
            payload["options"] = options

        # Return streaming response
        return StreamingResponse(
            ollama_proxy.chat_stream(payload),
            media_type="text/event-stream"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat stream failed: {str(e)}")
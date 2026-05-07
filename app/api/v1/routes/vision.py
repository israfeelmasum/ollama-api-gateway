"""Vision model endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.api.v1.schemas.vision import VisionChatRequest
from app.services.ollama_proxy import ollama_proxy

router = APIRouter()


@router.post("/chat")
async def vision_chat(request: VisionChatRequest):
    """
    Chat with vision model using image inputs.

    Accepts base64 encoded images.
    """
    try:
        # Prepare Ollama payload
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "images": request.images,
            "stream": False
        }

        # Add optional parameters
        options = {}
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens

        if options:
            payload["options"] = options

        # Call Ollama generate endpoint (used for vision)
        response = await ollama_proxy.generate(payload)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision chat failed: {str(e)}")


@router.post("/stream")
async def vision_stream(request: VisionChatRequest):
    """
    Stream vision model response.

    Returns Server-Sent Events (SSE) stream.
    """
    try:
        # Prepare Ollama payload
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "images": request.images,
            "stream": True
        }

        # Add optional parameters
        options = {}
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens

        if options:
            payload["options"] = options

        # Return streaming response
        return StreamingResponse(
            ollama_proxy.generate_stream(payload),
            media_type="text/event-stream"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision stream failed: {str(e)}")
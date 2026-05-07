"""Vision endpoint schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class VisionChatRequest(BaseModel):
    """Vision chat request with images."""
    model: str = Field(..., description="Vision model name")
    prompt: str = Field(..., description="Text prompt")
    images: List[str] = Field(..., description="Base64 encoded images")
    stream: bool = Field(default=False)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None)


class VisionChatResponse(BaseModel):
    """Vision chat response."""
    model: str
    created_at: str
    response: str
    done: bool
    total_duration: Optional[int] = None
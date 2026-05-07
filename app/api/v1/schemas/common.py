"""Common schemas used across endpoints."""

from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ModelInfo(BaseModel):
    """Model information."""
    name: str
    type: str
    capabilities: list[str]
    family: Optional[str] = None
    size: Optional[int] = None
    size_formatted: Optional[str] = None
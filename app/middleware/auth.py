"""Authentication middleware."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""

    # Public endpoints that don't require authentication
    PUBLIC_PATHS = ["/", "/docs", "/redoc", "/openapi.json", "/api/v1/health"]

    async def dispatch(self, request: Request, call_next):
        """Process request and verify authentication."""

        # Skip auth for public endpoints
        if not settings.require_api_key or request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Check for API key
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing API Key. Include 'X-API-Key' header or 'Authorization: Bearer <key>'."},
                headers={"WWW-Authenticate": "ApiKey"}
            )

        if api_key not in settings.api_keys_list:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API Key"}
            )

        # Add API key to request state for logging
        request.state.api_key = api_key

        response = await call_next(request)
        return response

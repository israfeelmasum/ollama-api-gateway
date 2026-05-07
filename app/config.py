"""Configuration management using Pydantic Settings."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama API"
    )
    ollama_timeout: int = Field(
        default=120,
        description="Request timeout in seconds",
        ge=1,
        le=600
    )

    # Authentication
    api_keys: str = Field(
        default="",
        description="Comma-separated list of valid API keys"
    )
    require_api_key: bool = Field(
        default=True,
        description="Whether to require API key authentication"
    )

    # Features
    auto_detect_model_type: bool = Field(
        default=True,
        description="Automatically detect model types from names"
    )
    enhance_responses: bool = Field(
        default=False,
        description="Add extra metadata to responses"
    )
    allow_raw_passthrough: bool = Field(
        default=True,
        description="Allow raw Ollama API passthrough"
    )

    # CORS
    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins"
    )

    # Server
    host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    port: int = Field(
        default=8000,
        description="Server port",
        ge=1,
        le=65535
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_url(cls, v: str) -> str:
        """Ensure Ollama URL doesn't end with slash."""
        return v.rstrip("/")

    @property
    def api_keys_list(self) -> List[str]:
        """Parse comma-separated API keys into a list."""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
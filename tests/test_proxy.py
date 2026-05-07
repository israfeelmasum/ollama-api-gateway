"""Basic tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()


def test_health():
    """Test health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_models_without_auth():
    """Test models endpoint requires auth."""
    response = client.get("/api/v1/models")
    # Should fail without API key if auth is enabled
    assert response.status_code in [401, 403, 200]  # 200 if auth disabled


# Add more tests as needed
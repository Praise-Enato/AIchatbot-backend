"""
Tests for the authentication middleware.
"""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from chatbot_backend.app import app


@pytest.fixture
def test_client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def api_secret():
    """Get the API secret."""
    return os.environ.get("API_SECRET", "secret_key")


def test_non_api_route_no_auth(test_client):
    """Test that non-API routes don't require authentication."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_api_route_no_auth_header(test_client):
    """Test API route without auth header."""
    response = test_client.post("/api/titles/generate", json={"message": "Test message"})
    assert response.status_code == 401
    assert "message" in response.json()
    assert "Invalid or missing API key" in response.json()["message"]


def test_api_route_invalid_auth_format(test_client):
    """Test API route with invalid auth format."""
    response = test_client.post(
        "/api/titles/generate", headers={"Authorization": "Invalid-Format"}, json={"message": "Test message"}
    )
    assert response.status_code == 401
    assert "message" in response.json()
    assert "Invalid or missing API key" in response.json()["message"]


def test_api_route_invalid_token(test_client):
    """Test API route with invalid token."""
    response = test_client.post(
        "/api/titles/generate", headers={"Authorization": "Bearer invalid-token"}, json={"message": "Test message"}
    )
    assert response.status_code == 401
    assert "message" in response.json()
    assert "Invalid or missing API key" in response.json()["message"]


def test_api_route_valid_token(test_client, api_secret):
    """Test API route with valid token."""
    # Mock the default_provider.get_response method to avoid making real API calls
    with patch("chatbot_backend.providers.factory.default_provider.get_response", return_value="Test Title"):
        response = test_client.post(
            "/api/titles/generate", headers={"Authorization": f"Bearer {api_secret}"}, json={"message": "Test message"}
        )
        assert response.status_code == 200
        assert response.json() == {"text": "Test Title"}

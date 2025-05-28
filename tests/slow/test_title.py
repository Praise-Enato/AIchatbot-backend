"""
Tests for the generate_title endpoint.
"""

import os

import pytest
from fastapi.testclient import TestClient

from chatbot_backend.app import app


@pytest.fixture
def test_client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Get the auth headers."""
    api_secret = os.environ.get("API_SECRET", "secret_key")
    return {"Authorization": f"Bearer {api_secret}"}


def test_generate_title_empty_message(test_client, auth_headers):
    """Test generate_title endpoint with empty message."""
    response = test_client.post("/api/titles/generate", headers=auth_headers, json={"text": ""})
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "empty" in response.json()["detail"].lower()


def test_generate_title_success(test_client, auth_headers):
    """Test generate_title endpoint with successful response (slow test - makes API call)."""
    test_message = "I need help setting up a Python development environment for a new web project."

    response = test_client.post("/api/titles/generate", headers=auth_headers, json={"text": test_message})

    assert response.status_code == 200
    assert "text" in response.json()

    # Check that the title is not empty and not too long
    title = response.json()["text"]
    assert title
    assert len(title) <= 80

    # Check that the title doesn't contain quotes or colons
    assert '"' not in title
    assert "'" not in title
    assert ":" not in title

    # Check that the title is relevant to the message
    assert any(keyword.lower() in title.lower() for keyword in ["Python", "development", "environment", "project"])

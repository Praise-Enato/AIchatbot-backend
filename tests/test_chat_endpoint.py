"""
Tests for the chat endpoint.
"""

import os
import uuid

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


@pytest.fixture
def chat_request_data():
    """Get chat request data."""
    return {
        "messages": [{"role": "user", "content": "Hello, how are you today?", "id": str(uuid.uuid4())}],
        "userId": "test-user",
        "userType": "guest",
        "chatId": str(uuid.uuid4()),
    }


def test_chat_endpoint_no_auth(test_client, chat_request_data):
    """Test chat endpoint without authentication."""
    response = test_client.post("/api/chat", json=chat_request_data)
    assert response.status_code == 401
    assert "message" in response.json()
    assert "Invalid or missing API key" in response.json()["message"]


@pytest.mark.slow
def test_chat_endpoint_success(test_client, auth_headers, chat_request_data):
    """Test chat endpoint with successful response (slow test - makes API call)."""
    response = test_client.post("/api/chat", headers=auth_headers, json=chat_request_data)

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    # Read the response content to verify format
    content = response.content.decode("utf-8")

    # Check the streaming format
    # Normal chunks should start with 0:" and end with "\n
    assert '0:"' in content

    # Check that chunks are properly formatted
    chunks = content.split("\n")
    for chunk in chunks[:-1]:  # Exclude the last empty chunk after split
        assert chunk.startswith('0:"') or chunk.startswith('3:"') or chunk == 'd:{"finishReason":"stop"}'

    # Check for the completion message
    assert 'd:{"finishReason":"stop"}' in content


def test_chat_endpoint_invalid_request(test_client, auth_headers):
    """Test chat endpoint with invalid request."""
    # Missing required fields
    invalid_data = {"messages": []}

    response = test_client.post("/api/chat", headers=auth_headers, json=invalid_data)

    assert response.status_code == 422  # Validation error

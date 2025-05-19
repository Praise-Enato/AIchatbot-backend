"""
Tests for the chat endpoint.
"""

import json
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
    chunks = content.split("\n")

    # Check for the first chunk with message ID
    first_chunk = chunks[0]
    assert first_chunk.startswith('f:{"messageId":"')
    assert first_chunk.endswith('"}')

    # Verify messageId format (should be UUID)
    message_id_data = json.loads(first_chunk.replace("f:", ""))
    assert "messageId" in message_id_data
    assert len(message_id_data["messageId"]) == 36  # UUID length

    # Check that normal chunks are properly formatted
    # Start from index 1 to skip the first message ID chunk
    for chunk in chunks[1:-2]:  # Exclude the first chunk, last chunk and the empty chunk after split
        if chunk.startswith("0:"):
            assert chunk.startswith('0:"')

    # Check for the completion message with usage information
    finish_chunk = chunks[-2]
    assert "finishReason" in finish_chunk

    # Check for usage information in the completion message
    # The actual usage information may vary, but tokens should be meaningful
    assert "usage" in finish_chunk

    # Convert JSON string to dict to check token values
    finish_data = json.loads(finish_chunk.replace("d:", ""))

    # Check that token counts are present and have reasonable values
    assert "promptTokens" in finish_data["usage"]
    assert "completionTokens" in finish_data["usage"]

    # Ensure token counts are greater than 10
    prompt_tokens = finish_data["usage"]["promptTokens"]
    assert prompt_tokens > 10, f"Expected promptTokens > 10, got: {prompt_tokens}"
    completion_tokens = finish_data["usage"]["completionTokens"]
    assert completion_tokens > 10, f"Expected completionTokens > 10, got: {completion_tokens}"


def test_chat_endpoint_invalid_request(test_client, auth_headers):
    """Test chat endpoint with invalid request."""
    # Missing required fields
    invalid_data = {"messages": []}

    response = test_client.post("/api/chat", headers=auth_headers, json=invalid_data)

    assert response.status_code == 422  # Validation error

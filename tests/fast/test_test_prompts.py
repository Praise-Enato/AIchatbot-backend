"""
Tests for test prompt functionality.
"""

import json
import time

import pytest
from fastapi.testclient import TestClient

from chatbot_backend.app import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Get auth headers for testing."""
    return {"Authorization": "Bearer secret_key"}


def test_generate_title_with_test_prompt_1(client, auth_headers):
    """Test that 'Test prompt 1' returns 'Test title 1'."""
    response = client.post("/api/titles/generate", json={"text": "Test prompt 1"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"text": "Test title 1"}


def test_chat_streaming_with_test_prompt_1(client, auth_headers):
    """Test that 'Test prompt 1' streams the correct response."""
    start_time = time.time()

    response = client.post(
        "/api/chats/test-chat-1/responses",
        json={
            "messages": [{"role": "user", "parts": [{"type": "text", "text": "Test prompt 1"}], "id": "test-msg-1"}],
            "userId": "test-user",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Parse the streamed response
    content = response.content.decode("utf-8")
    lines = content.strip().split("\n")

    # Check first chunk is message ID
    assert lines[0].startswith('f:{"messageId":"')

    # Check we get the expected tokens
    expected_tokens = ["Test ", "Response ", "1"]
    token_lines = []

    for line in lines[1:]:
        if line.startswith("0:"):
            # Extract the token from the JSON
            token_data = line[2:]  # Remove "0:" prefix
            token = json.loads(token_data)
            token_lines.append(token)

    assert token_lines == expected_tokens

    # Check timing - should take at least 200ms for 3 tokens with 100ms delays
    elapsed = time.time() - start_time
    assert elapsed >= 0.2  # Allow some margin for processing

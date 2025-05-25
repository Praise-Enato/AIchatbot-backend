"""
Tests for stream operations.

This module tests stream creation, retrieval, and related error scenarios.
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


def test_create_and_get_streams(test_client, auth_headers):
    """Test creating a stream and verifying it appears in chat streams list."""
    # First, create a user
    email = f"test-{uuid.uuid4()}@example.com"
    password_hash = "test-password-hash"

    user_response = test_client.post(
        "/api/users", json={"email": email, "passwordHash": password_hash}, headers=auth_headers
    )
    assert user_response.status_code == 201
    user = user_response.json()
    user_id = user["userId"]

    # Create a chat for this user
    chat_id = str(uuid.uuid4())
    chat_title = "Test Chat for Streams"

    chat_response = test_client.post(
        "/api/chats",
        json={"chatId": chat_id, "userId": user_id, "title": chat_title, "visibility": "private"},
        headers=auth_headers,
    )
    assert chat_response.status_code == 201

    # Check initial streams (should be empty)
    initial_streams_response = test_client.get(f"/api/chats/{chat_id}/streams", headers=auth_headers)
    assert initial_streams_response.status_code == 200
    initial_streams = initial_streams_response.json()
    assert len(initial_streams["streamIds"]) == 0

    # Create a stream
    stream_id = str(uuid.uuid4())

    create_stream_response = test_client.post(
        f"/api/chats/{chat_id}/streams",
        json={"streamId": stream_id},
        headers=auth_headers,
    )
    assert create_stream_response.status_code == 201
    created_stream = create_stream_response.json()
    assert created_stream["streamId"] == stream_id
    assert created_stream["chatId"] == chat_id
    assert "createdAt" in created_stream

    # Verify stream appears in chat streams list
    final_streams_response = test_client.get(f"/api/chats/{chat_id}/streams", headers=auth_headers)
    assert final_streams_response.status_code == 200
    final_streams = final_streams_response.json()
    assert len(final_streams["streamIds"]) == 1
    assert final_streams["streamIds"][0] == stream_id

    # Create a second stream to verify multiple streams work
    stream_id_2 = str(uuid.uuid4())

    create_stream_2_response = test_client.post(
        f"/api/chats/{chat_id}/streams",
        json={"streamId": stream_id_2},
        headers=auth_headers,
    )
    assert create_stream_2_response.status_code == 201

    # Verify both streams appear in the list
    multi_streams_response = test_client.get(f"/api/chats/{chat_id}/streams", headers=auth_headers)
    assert multi_streams_response.status_code == 200
    multi_streams = multi_streams_response.json()
    assert len(multi_streams["streamIds"]) == 2
    assert stream_id in multi_streams["streamIds"]
    assert stream_id_2 in multi_streams["streamIds"]


def test_create_multiple_streams_different_chats(test_client, auth_headers):
    """Test creating streams in different chats."""
    # Create a user
    email = f"test-{uuid.uuid4()}@example.com"
    password_hash = "test-password-hash"

    user_response = test_client.post(
        "/api/users", json={"email": email, "passwordHash": password_hash}, headers=auth_headers
    )
    assert user_response.status_code == 201
    user = user_response.json()
    user_id = user["userId"]

    # Create two different chats
    chat_id_1 = str(uuid.uuid4())
    chat_id_2 = str(uuid.uuid4())

    for chat_id in [chat_id_1, chat_id_2]:
        chat_response = test_client.post(
            "/api/chats",
            json={"chatId": chat_id, "userId": user_id, "title": f"Chat {chat_id}", "visibility": "private"},
            headers=auth_headers,
        )
        assert chat_response.status_code == 201

    # Create streams in each chat
    stream_id_1 = str(uuid.uuid4())
    stream_id_2 = str(uuid.uuid4())

    # Stream in first chat
    response_1 = test_client.post(
        f"/api/chats/{chat_id_1}/streams",
        json={"streamId": stream_id_1},
        headers=auth_headers,
    )
    assert response_1.status_code == 201

    # Stream in second chat
    response_2 = test_client.post(
        f"/api/chats/{chat_id_2}/streams",
        json={"streamId": stream_id_2},
        headers=auth_headers,
    )
    assert response_2.status_code == 201

    # Verify each chat has only its own stream
    streams_1_response = test_client.get(f"/api/chats/{chat_id_1}/streams", headers=auth_headers)
    assert streams_1_response.status_code == 200
    streams_1 = streams_1_response.json()
    assert len(streams_1["streamIds"]) == 1
    assert streams_1["streamIds"][0] == stream_id_1

    streams_2_response = test_client.get(f"/api/chats/{chat_id_2}/streams", headers=auth_headers)
    assert streams_2_response.status_code == 200
    streams_2 = streams_2_response.json()
    assert len(streams_2["streamIds"]) == 1
    assert streams_2["streamIds"][0] == stream_id_2


# Error handling tests for stream operations


def test_invalid_data_create_stream(test_client, auth_headers):
    """Test creating stream with invalid data."""
    chat_id = str(uuid.uuid4())

    # Missing stream ID
    response = test_client.post(
        f"/api/chats/{chat_id}/streams",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Invalid stream ID type
    response = test_client.post(
        f"/api/chats/{chat_id}/streams",
        json={"streamId": 123},  # Should be string
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_stream_operations_with_nonexistent_chat(test_client, auth_headers):
    """Test stream operations with non-existent chat."""
    non_existent_chat_id = str(uuid.uuid4())

    # Get streams for non-existent chat
    response = test_client.get(f"/api/chats/{non_existent_chat_id}/streams", headers=auth_headers)
    assert response.status_code == 200  # Returns empty list, not 404
    assert response.json()["streamIds"] == []

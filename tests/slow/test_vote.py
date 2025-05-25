"""
Tests for vote operations.

This module tests message voting functionality and related error scenarios.
"""

import os
import uuid
from datetime import UTC, datetime

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


def test_vote_on_message(test_client, auth_headers):
    """Test creating a message and voting on it, verifying vote appears in chat votes."""
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
    chat_title = "Test Chat for Voting"

    chat_response = test_client.post(
        "/api/chats",
        json={"chatId": chat_id, "userId": user_id, "title": chat_title, "visibility": "private"},
        headers=auth_headers,
    )
    assert chat_response.status_code == 201

    # Create and save a message to vote on
    message_id = str(uuid.uuid4())
    created_at = datetime.now(UTC).isoformat()

    messages_data = [
        {
            "chatId": chat_id,
            "createdAt": created_at,
            "role": "assistant",
            "parts": ["This is a message to vote on"],
            "attachments": [],
            "messageId": message_id,
        }
    ]

    # Save messages via POST /api/chats/{chat_id}/messages
    save_messages_response = test_client.post(
        f"/api/chats/{chat_id}/messages",
        json={"userId": user_id, "messages": messages_data},
        headers=auth_headers,
    )
    assert save_messages_response.status_code == 201

    # Check initial votes (should be empty)
    initial_votes_response = test_client.get(f"/api/chats/{chat_id}/votes", headers=auth_headers)
    assert initial_votes_response.status_code == 200
    initial_votes = initial_votes_response.json()
    assert len(initial_votes) == 0

    # Vote on the message via POST /api/chats/{chat_id}/messages/{message_id}/vote
    vote_response = test_client.post(
        f"/api/chats/{chat_id}/messages/{message_id}/vote",
        json={"voteType": "up"},
        headers=auth_headers,
    )
    assert vote_response.status_code == 201

    # Verify vote appears in chat votes via GET /api/chats/{chat_id}/votes
    final_votes_response = test_client.get(f"/api/chats/{chat_id}/votes", headers=auth_headers)
    assert final_votes_response.status_code == 200
    final_votes = final_votes_response.json()
    assert len(final_votes) == 1

    vote = final_votes[0]
    assert vote["chatId"] == chat_id
    assert vote["messageId"] == message_id
    assert vote["isUpvoted"]


def test_vote_down_on_message(test_client, auth_headers):
    """Test voting down on a message."""
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
    chat_title = "Test Chat for Down Voting"

    chat_response = test_client.post(
        "/api/chats",
        json={"chatId": chat_id, "userId": user_id, "title": chat_title, "visibility": "private"},
        headers=auth_headers,
    )
    assert chat_response.status_code == 201

    # Create and save a message to vote on
    message_id = str(uuid.uuid4())
    created_at = datetime.now(UTC).isoformat()

    messages_data = [
        {
            "chatId": chat_id,
            "createdAt": created_at,
            "role": "assistant",
            "parts": ["This is a message to vote down"],
            "attachments": [],
            "messageId": message_id,
        }
    ]

    # Save messages
    save_messages_response = test_client.post(
        f"/api/chats/{chat_id}/messages",
        json={"userId": user_id, "messages": messages_data},
        headers=auth_headers,
    )
    assert save_messages_response.status_code == 201

    # Vote down on the message
    vote_response = test_client.post(
        f"/api/chats/{chat_id}/messages/{message_id}/vote",
        json={"voteType": "down"},
        headers=auth_headers,
    )
    assert vote_response.status_code == 201

    # Verify vote appears with correct down vote
    final_votes_response = test_client.get(f"/api/chats/{chat_id}/votes", headers=auth_headers)
    assert final_votes_response.status_code == 200
    final_votes = final_votes_response.json()
    assert len(final_votes) == 1

    vote = final_votes[0]
    assert vote["chatId"] == chat_id
    assert vote["messageId"] == message_id
    assert not vote["isUpvoted"]


# Error handling tests for vote operations


def test_invalid_data_vote_message(test_client, auth_headers):
    """Test voting with invalid data."""
    chat_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    # Invalid vote type
    response = test_client.post(
        f"/api/chats/{chat_id}/messages/{message_id}/vote",
        json={"voteType": "invalid_vote"},  # Should be 'up' or 'down'
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Missing vote type
    response = test_client.post(
        f"/api/chats/{chat_id}/messages/{message_id}/vote",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_vote_operations_with_nonexistent_chat(test_client, auth_headers):
    """Test vote operations with non-existent chat."""
    non_existent_chat_id = str(uuid.uuid4())

    # Get votes for non-existent chat
    response = test_client.get(f"/api/chats/{non_existent_chat_id}/votes", headers=auth_headers)
    assert response.status_code == 200  # Returns empty list, not 404
    assert response.json() == []

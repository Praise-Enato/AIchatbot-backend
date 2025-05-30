"""
Tests for user operations.

This module tests user CRUD operations, OAuth functionality,
and related error scenarios.
"""

import json
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


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
def test_data_generator():
    """Test data generator fixture."""

    class TestDataGenerator:
        @staticmethod
        def unique_email():
            return f"test-{uuid.uuid4()}@example.com"

        @staticmethod
        def test_password_hash():
            return "test-password-hash"

        @staticmethod
        def oauth_provider_data():
            return {"provider": "google", "providerAccountId": str(uuid.uuid4())}

        @staticmethod
        def unique_id():
            return str(uuid.uuid4())

    return TestDataGenerator()


def test_create_and_get_user_with_password(test_client, test_data_generator, auth_headers):
    """Test creating a user with email/password and retrieving it."""
    # Generate test data
    email = test_data_generator.unique_email()
    password_hash = test_data_generator.test_password_hash()

    # Create user via POST /api/users
    create_response = test_client.post(
        "/api/users", json={"email": email, "passwordHash": password_hash}, headers=auth_headers
    )

    # Verify creation response
    assert create_response.status_code == 201
    created_user = create_response.json()
    assert created_user["email"] == email
    assert created_user["source"] == "email"
    assert "id" in created_user
    assert "createdAt" in created_user
    assert "passwordHash" in created_user

    # Retrieve user via GET /api/users/{email}
    get_response = test_client.get(f"/api/users/{email}", headers=auth_headers)

    # Verify retrieval response
    assert get_response.status_code == 200
    retrieved_user = get_response.json()
    assert retrieved_user["email"] == email
    assert retrieved_user["source"] == "email"
    assert retrieved_user["id"] == created_user["id"]
    assert retrieved_user["createdAt"] == created_user["createdAt"]
    assert retrieved_user["passwordHash"] == password_hash


def test_create_and_get_guest_user(test_client, auth_headers):
    """Test creating a guest user and retrieving it."""
    # Create guest user via POST /api/users/guest
    create_response = test_client.post("/api/users/guest", headers=auth_headers)

    # Verify creation response
    assert create_response.status_code == 201
    created_user = create_response.json()
    print(f"Created user: {json.dumps(created_user, indent=4)}")
    assert created_user["source"] == "guest"
    assert "id" in created_user
    assert "email" in created_user
    assert "createdAt" in created_user

    # Extract email for retrieval
    guest_email = created_user["email"]

    # Retrieve user via GET /api/users/{email}
    get_response = test_client.get(f"/api/users/{guest_email}", headers=auth_headers)

    # Verify retrieval response
    assert get_response.status_code == 200
    retrieved_user = get_response.json()
    print(f"Retrieved user: {json.dumps(retrieved_user, indent=4)}")
    assert retrieved_user["email"] == guest_email
    assert retrieved_user["source"] == "guest"
    assert retrieved_user["id"] == created_user["id"]
    assert retrieved_user["createdAt"] == created_user["createdAt"]
    assert "passwordHash" not in retrieved_user


def test_create_and_get_oauth_user(test_client, test_data_generator, auth_headers):
    """Test creating an OAuth user and retrieving it."""
    # Generate test data
    email = test_data_generator.unique_email()
    oauth_data = test_data_generator.oauth_provider_data()

    # Create OAuth user via POST /api/users/oauth
    create_response = test_client.post(
        "/api/users/oauth",
        json={"email": email, "provider": oauth_data["provider"], "providerAccountId": oauth_data["providerAccountId"]},
        headers=auth_headers,
    )

    # Verify creation response
    assert create_response.status_code == 201
    created_user = create_response.json()
    assert created_user["email"] == email
    assert created_user["source"] == "oauth"
    assert created_user["provider"] == oauth_data["provider"]
    assert created_user["providerAccountId"] == oauth_data["providerAccountId"]
    assert "id" in created_user
    assert "createdAt" in created_user
    assert "passwordHash" not in created_user

    # Retrieve user via GET /api/users/{email}
    get_response = test_client.get(f"/api/users/{email}", headers=auth_headers)

    # Verify retrieval response
    assert get_response.status_code == 200
    retrieved_user = get_response.json()
    assert retrieved_user["email"] == email
    assert retrieved_user["source"] == "oauth"
    assert retrieved_user["provider"] == oauth_data["provider"]
    assert retrieved_user["providerAccountId"] == oauth_data["providerAccountId"]
    assert retrieved_user["id"] == created_user["id"]
    assert retrieved_user["createdAt"] == created_user["createdAt"]
    assert "passwordHash" not in retrieved_user


def test_create_chat_appears_in_user_chats(test_client, test_data_generator, auth_headers):
    """Test creating a chat and verifying it appears in user's chat list."""
    # First, create a user
    email = test_data_generator.unique_email()
    password_hash = test_data_generator.test_password_hash()

    user_response = test_client.post(
        "/api/users", json={"email": email, "passwordHash": password_hash}, headers=auth_headers
    )
    assert user_response.status_code == 201
    user = user_response.json()
    user_id = user["id"]

    # Create a chat for this user
    chat_id = test_data_generator.unique_id()
    chat_title = "Test Chat"

    chat_response = test_client.post(
        "/api/chats",
        json={"id": chat_id, "userId": user_id, "title": chat_title, "visibility": "private"},
        headers=auth_headers,
    )
    assert chat_response.status_code == 201
    created_chat = chat_response.json()
    assert created_chat["id"] == chat_id
    assert created_chat["userId"] == user_id
    assert created_chat["title"] == chat_title
    assert created_chat["visibility"] == "private"

    # Get user's chats via GET /api/users/{user_id}/chats
    chats_response = test_client.get(f"/api/users/{user_id}/chats", headers=auth_headers)
    assert chats_response.status_code == 200

    chats_data = chats_response.json()
    assert "chats" in chats_data
    assert len(chats_data["chats"]) == 1

    # Verify the chat appears in the list with correct data
    chat_in_list = chats_data["chats"][0]
    assert chat_in_list["id"] == chat_id
    assert chat_in_list["userId"] == user_id
    assert chat_in_list["title"] == chat_title
    assert chat_in_list["visibility"] == "private"
    assert "createdAt" in chat_in_list


# Error handling tests for user operations


def test_get_nonexistent_user_returns_404(test_client, test_data_generator, auth_headers):
    """Test that getting a non-existent user returns 404."""
    nonexistent_email = test_data_generator.unique_email()

    response = test_client.get(f"/api/users/{nonexistent_email}", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_user_with_duplicate_email_handling(test_client, test_data_generator, auth_headers):
    """Test creating users with duplicate emails (should handle gracefully)."""
    email = test_data_generator.unique_email()
    password_hash = test_data_generator.test_password_hash()

    # Create first user
    first_response = test_client.post(
        "/api/users", json={"email": email, "passwordHash": password_hash}, headers=auth_headers
    )
    assert first_response.status_code == 201

    # Try to create second user with same email
    # This should fail gracefully
    second_response = test_client.post(
        "/api/users", json={"email": email, "passwordHash": password_hash}, headers=auth_headers
    )

    # Accept 4xx error (conflict)
    assert second_response.status_code == 409


def test_invalid_user_creation_data(test_client, auth_headers):
    """Test user creation with invalid data."""
    # Missing required fields
    response = test_client.post(
        "/api/users",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 422  # Unprocessable Entity

    # Invalid field types
    response = test_client.post(
        "/api/users",
        json={
            "email": 123,  # Should be string
            "passwordHash": "valid-hash",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Empty email string
    response = test_client.post(
        "/api/users",
        json={
            "email": "",  # Empty string
            "passwordHash": "valid-hash",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_invalid_oauth_user_creation_data(test_client, auth_headers):
    """Test OAuth user creation with invalid data."""
    # Missing required provider fields
    response = test_client.post(
        "/api/users/oauth",
        json={"email": "test@example.com"},  # Missing provider and providerAccountId
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Empty provider string
    response = test_client.post(
        "/api/users/oauth",
        json={
            "email": "test@example.com",
            "provider": "",  # Empty string
            "providerAccountId": "valid-id",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422

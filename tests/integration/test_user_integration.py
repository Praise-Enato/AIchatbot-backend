"""
Integration tests for user routes.

These tests verify end-to-end functionality of user operations
including creation, retrieval, and OAuth user management.
"""

import json

import pytest


@pytest.mark.slow
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
    assert "userId" in created_user
    assert "createdAt" in created_user
    assert "passwordHash" in created_user

    # Retrieve user via GET /api/users/{email}
    get_response = test_client.get(f"/api/users/{email}", headers=auth_headers)

    # Verify retrieval response
    assert get_response.status_code == 200
    retrieved_user = get_response.json()
    assert retrieved_user["email"] == email
    assert retrieved_user["source"] == "email"
    assert retrieved_user["userId"] == created_user["userId"]
    assert retrieved_user["createdAt"] == created_user["createdAt"]
    assert retrieved_user["passwordHash"] == password_hash


@pytest.mark.slow
def test_create_and_get_guest_user(test_client, auth_headers):
    """Test creating a guest user and retrieving it."""
    # Create guest user via POST /api/users/guest
    create_response = test_client.post("/api/users/guest", headers=auth_headers)

    # Verify creation response
    assert create_response.status_code == 201
    created_user = create_response.json()
    print(f"Created user: {json.dumps(created_user, indent=4)}")
    assert created_user["source"] == "guest"
    assert "userId" in created_user
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
    assert retrieved_user["userId"] == created_user["userId"]
    assert retrieved_user["createdAt"] == created_user["createdAt"]
    assert "passwordHash" not in retrieved_user


@pytest.mark.slow
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
    assert "userId" in created_user
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
    assert retrieved_user["userId"] == created_user["userId"]
    assert retrieved_user["createdAt"] == created_user["createdAt"]
    assert "passwordHash" not in retrieved_user


@pytest.mark.slow
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
    user_id = user["userId"]

    # Create a chat for this user
    chat_id = test_data_generator.unique_id()
    chat_title = "Test Chat"

    chat_response = test_client.post(
        "/api/chats",
        json={"chatId": chat_id, "userId": user_id, "title": chat_title, "visibility": "private"},
        headers=auth_headers,
    )
    assert chat_response.status_code == 201
    created_chat = chat_response.json()
    assert created_chat["chatId"] == chat_id
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
    assert chat_in_list["chatId"] == chat_id
    assert chat_in_list["userId"] == user_id
    assert chat_in_list["title"] == chat_title
    assert chat_in_list["visibility"] == "private"
    assert "chatCreatedAt" in chat_in_list


@pytest.mark.slow
def test_get_nonexistent_user_returns_404(test_client, test_data_generator, auth_headers):
    """Test that getting a non-existent user returns 404."""
    nonexistent_email = test_data_generator.unique_email()

    response = test_client.get(f"/api/users/{nonexistent_email}", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.slow
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

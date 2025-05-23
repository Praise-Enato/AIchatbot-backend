"""
User management routes for the chatbot backend.

This module provides API endpoints for user operations including creation,
retrieval, and OAuth user management.
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import ValidationError

from chatbot_backend import db
from chatbot_backend.custom_logger import get_logger
from chatbot_backend.models.chat import (
    ChatListResponse,
    CreateOAuthUserRequest,
    CreateUserRequest,
    MessageCountResponse,
)
from chatbot_backend.models.user import User

# Configure logging
logger = get_logger("user_routes")

# Create a router for user endpoints
router = APIRouter(prefix="/api")


@router.get("/users/{email}", response_model=User)
async def get_user_by_email(email: str) -> User:
    """Get user by email address."""
    try:
        user = db.get_user(email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with email '{email}' not found")
        return user
    except Exception as err:
        logger.error("Failed to get user by email %s: %s", email, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(request: CreateUserRequest) -> User:
    """Create a new regular user."""
    try:
        user = db.create_user(request.email, request.password)
        return user
    except ValidationError as err:
        logger.error("Validation error creating user: %s", err)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid user data") from err
    except Exception as err:
        logger.error("Failed to create user %s: %s", request.email, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.post("/users/guest", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_guest_user() -> User:
    """Create a new guest user."""
    try:
        user = db.create_guest_user()
        return user
    except Exception as err:
        logger.error("Failed to create guest user: %s", err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.post("/users/oauth", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_oauth_user(request: CreateOAuthUserRequest) -> User:
    """Create or get a user via OAuth."""
    try:
        user = db.get_or_create_user_from_oauth(request.email, request.provider, request.provider_account_id)
        return user
    except ValidationError as err:
        logger.error("Validation error creating OAuth user: %s", err)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid OAuth user data") from err
    except Exception as err:
        logger.error("Failed to create OAuth user: %s", err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.get("/users/{user_id}/chats", response_model=ChatListResponse)
async def get_user_chats(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    starting_after: str | None = Query(default=None),
    ending_before: str | None = Query(default=None),
) -> ChatListResponse:
    """Get chats for a user with pagination."""
    try:
        return db.get_chats_by_user_id(user_id, limit, starting_after, ending_before)
    except Exception as err:
        logger.error("Failed to get chats for user %s: %s", user_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.get("/users/{user_id}/message-count", response_model=MessageCountResponse)
async def get_user_message_count(
    user_id: str, hours: int = Query(default=24, ge=1, description="Number of hours to look back")
) -> MessageCountResponse:
    """Get message count for a user in the last N hours."""
    try:
        count = db.get_message_count_by_user_id(user_id, hours)
        return MessageCountResponse(count=count)
    except Exception as err:
        logger.error("Failed to get message count for user %s: %s", user_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err

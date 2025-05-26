"""
Chat routes for the chatbot backend.

This module contains the routes for chat-related endpoints.
"""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from chatbot_backend.custom_logger import get_logger
from chatbot_backend.db.chat import (
    create_stream_id,
    delete_chat_by_id,
    delete_messages_by_chat_id_after_timestamp,
    get_chat_by_id,
    get_message_by_id,
    get_messages_by_chat_id,
    get_stream_ids_by_chat_id,
    get_votes_by_chat_id,
    save_chat,
    save_messages,
    update_chat_visibility_by_id,
    vote_message,
)
from chatbot_backend.models.chat import (
    Chat,
    ChatRequest,
    CreateChatRequest,
    CreateStreamRequest,
    Message,
    SaveMessagesRequest,
    Stream,
    StreamIdsResponse,
    UpdateChatVisibilityRequest,
    Vote,
    VoteMessageRequest,
)
from chatbot_backend.models.common import ErrorResponse
from chatbot_backend.prompts import CHAT_SYSTEM_PROMPT
from chatbot_backend.providers.factory import default_provider
from chatbot_backend.utils import create_streaming_response

# Configure logging
logger = get_logger("chat_route")

# Create a router for the chat endpoints
router = APIRouter()


@router.post(
    "/api/chats/{chat_id}/responses",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def handle_chat_data(chat_id: str, request: ChatRequest) -> StreamingResponse:  # noqa: ARG001
    """
    Chat endpoint that processes messages and returns a streaming response.

    Args:
        chat_id: The ID of the chat (not currently used)
        request: The chat request containing messages and metadata.

    Returns:
        A streaming response with chat completions.
    """
    try:
        # Format messages for the provider
        provider_messages = default_provider.format_messages_from_request(request)

        # Create a streaming response
        async def generate() -> AsyncGenerator[str | dict, None]:
            try:
                chunk_count = 0
                for chunk in default_provider.stream_chat_response(
                    provider_messages, system_message=CHAT_SYSTEM_PROMPT
                ):
                    # Only count text chunks, not usage information
                    if isinstance(chunk, str):
                        chunk_count += 1
                    yield chunk
                logger.info(f"Generation complete - yielded {chunk_count} text chunks")
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                yield f"Error: {e}"

        # Return a streaming response with the correct media type
        response = create_streaming_response(generate())
        return response

    except Exception as e:
        # Log the error
        logger.error(f"Error processing chat request: {e}")

        # Raise an HTTPException that FastAPI will handle
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing request: {e}"
        ) from e


# Database endpoints for chats, messages, votes, and streams


@router.get("/api/chats/{chat_id}", response_model=Chat, response_model_exclude_none=True)
async def get_chat(chat_id: str) -> Chat:
    """Get chat by ID."""
    try:
        chat = get_chat_by_id(chat_id)
    except Exception as err:
        logger.error("Failed to get chat %s: %s", chat_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with ID '{chat_id}' not found")
    return chat


@router.post("/api/chats", response_model=Chat, status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
async def create_chat(request: CreateChatRequest) -> Chat:
    """Create a new chat."""
    try:
        return save_chat(request.chat_id, request.user_id, request.title, request.visibility)
    except ValidationError as err:
        logger.error("Validation error creating chat: %s", err)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid chat data") from err
    except Exception as err:
        logger.error("Failed to create chat: %s", err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.delete("/api/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(chat_id: str) -> None:
    """Delete a chat and all its related items."""
    try:
        delete_chat_by_id(chat_id)
    except Exception as err:
        logger.error("Failed to delete chat %s: %s", chat_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.patch("/api/chats/{chat_id}/visibility", status_code=status.HTTP_204_NO_CONTENT)
async def update_chat_visibility(chat_id: str, request: UpdateChatVisibilityRequest) -> None:
    """Update chat visibility."""
    try:
        update_chat_visibility_by_id(chat_id, request.visibility)
    except Exception as err:
        logger.error("Failed to update chat visibility %s: %s", chat_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.get("/api/chats/{chat_id}/messages", response_model=list[Message], response_model_exclude_none=True)
async def get_chat_messages(chat_id: str) -> list[Message]:
    """Get all messages for a chat."""
    try:
        return get_messages_by_chat_id(chat_id)
    except Exception as err:
        logger.error("Failed to get messages for chat %s: %s", chat_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.get("/api/messages/{message_id}", response_model=Message, response_model_exclude_none=True)
async def get_message(message_id: str) -> Message:
    """Get a specific message by ID."""
    try:
        message = get_message_by_id(message_id)
    except Exception as err:
        logger.error("Failed to get message %s: %s", message_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Message with ID '{message_id}' not found")
    return message


@router.post("/api/chats/{chat_id}/messages", status_code=status.HTTP_201_CREATED)
async def save_chat_messages(chat_id: str, request: SaveMessagesRequest) -> None:
    """Save messages to a chat."""
    try:
        save_messages(request.user_id, request.messages)
    except ValidationError as err:
        logger.error("Validation error saving messages: %s", err)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid message data") from err
    except Exception as err:
        logger.error("Failed to save messages to chat %s: %s", chat_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.delete("/api/chats/{chat_id}/messages", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_messages_after_timestamp(
    chat_id: str, timestamp: str = Query(description="ISO timestamp to delete messages after")
) -> None:
    """Delete messages after a given timestamp."""
    try:
        # Validate timestamp format but keep as string
        from datetime import datetime

        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))  # Just for validation
        delete_messages_by_chat_id_after_timestamp(chat_id, timestamp)
    except ValueError as err:
        logger.error("Invalid timestamp format: %s", err)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid timestamp format. Use ISO format."
        ) from err
    except Exception as err:
        logger.error("Failed to delete messages for chat %s: %s", chat_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.post("/api/chats/{chat_id}/messages/{message_id}/vote", status_code=status.HTTP_201_CREATED)
async def vote_on_message(chat_id: str, message_id: str, request: VoteMessageRequest) -> None:
    """Vote on a message."""
    try:
        vote_message(chat_id, message_id, request.vote_type)
    except ValidationError as err:
        logger.error("Validation error voting on message: %s", err)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid vote data") from err
    except Exception as err:
        logger.error("Failed to vote on message %s: %s", message_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.get("/api/chats/{chat_id}/votes", response_model=list[Vote], response_model_exclude_none=True)
async def get_chat_votes(chat_id: str) -> list[Vote]:
    """Get all votes for a chat."""
    try:
        return get_votes_by_chat_id(chat_id)
    except Exception as err:
        logger.error("Failed to get votes for chat %s: %s", chat_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.post(
    "/api/chats/{chat_id}/streams",
    response_model=Stream,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
async def create_stream(chat_id: str, request: CreateStreamRequest) -> Stream:
    """Create a stream ID for a chat."""
    try:
        return create_stream_id(request.stream_id, chat_id)
    except ValidationError as err:
        logger.error("Validation error creating stream: %s", err)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid stream data") from err
    except Exception as err:
        logger.error("Failed to create stream for chat %s: %s", chat_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err


@router.get("/api/chats/{chat_id}/streams", response_model=StreamIdsResponse, response_model_exclude_none=True)
async def get_chat_streams(chat_id: str) -> StreamIdsResponse:
    """Get all stream IDs for a chat."""
    try:
        stream_ids = get_stream_ids_by_chat_id(chat_id)
        return StreamIdsResponse(stream_ids=stream_ids)
    except Exception as err:
        logger.error("Failed to get streams for chat %s: %s", chat_id, err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from err

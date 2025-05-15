"""
Chat routes for the chatbot backend.

This module contains the routes for chat-related endpoints.
"""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from chatbot_backend.custom_logger import get_logger
from chatbot_backend.models.chat import ChatRequest
from chatbot_backend.models.common import ErrorResponse
from chatbot_backend.prompts import CHAT_SYSTEM_PROMPT
from chatbot_backend.providers.factory import default_provider
from chatbot_backend.utils import create_streaming_response

# Configure logging
logger = get_logger("chat_route")

# Create a router for the chat endpoints
router = APIRouter()


@router.post(
    "/api/chat",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def handle_chat_data(request: ChatRequest) -> StreamingResponse:
    """
    Chat endpoint that processes messages and returns a streaming response.

    Args:
        request: The chat request containing messages and metadata.

    Returns:
        A streaming response with chat completions.
    """
    try:
        # Format messages for the provider
        provider_messages = default_provider.format_messages_from_request(request)

        # Create a streaming response
        async def generate() -> AsyncGenerator[str, None]:
            try:
                chunk_count = 0
                for chunk in default_provider.stream_chat_response(
                    provider_messages, system_message=CHAT_SYSTEM_PROMPT
                ):
                    chunk_count += 1
                    yield chunk
                logger.info(f"Generation complete - yielded {chunk_count} chunks")
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

"""
Title generation routes for the chatbot backend.

This module contains the routes for title generation endpoints.
"""

from fastapi import APIRouter, HTTPException, status

from chatbot_backend.custom_logger import get_logger
from chatbot_backend.models.common import ErrorResponse, TextResponse
from chatbot_backend.models.title import GenerateTitleRequest
from chatbot_backend.prompts import GENERATE_TITLE_PROMPT
from chatbot_backend.providers.factory import default_provider
from chatbot_backend.providers.test import TEST_PROMPTS, test_provider

# Configure logging
logger = get_logger("title_route")

# Create a router for the title endpoints
router = APIRouter()


@router.post(
    "/api/titles/generate",
    response_model=TextResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def generate_title(request: GenerateTitleRequest) -> TextResponse:
    """
    Generate a title based on a user message.

    This endpoint takes a user message and generates a short, descriptive title
    using an LLM provider. The title is returned as a text response.

    Args:
        request: The request containing the user message.
        req: The FastAPI request object.

    Returns:
        A text response containing the generated title.
    """
    # Extract the message text
    message_text = request.text

    # Check for empty message before the try block
    if not message_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    try:
        # Use test provider for test prompts, default provider otherwise
        provider = test_provider if message_text in TEST_PROMPTS else default_provider

        # Call the get_response function with the system prompt and user message
        title = provider.get_response(system_message=GENERATE_TITLE_PROMPT, user_message=message_text)

        # Log the generated title
        logger.info(
            "Generated title",
            extra={
                "title": title,
            },
        )

        return TextResponse(text=title)

    except Exception as e:
        # Log the error
        logger.error(f"Error generating title: {e}")

        # Raise an HTTPException that FastAPI will handle
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating title: {e}"
        ) from e

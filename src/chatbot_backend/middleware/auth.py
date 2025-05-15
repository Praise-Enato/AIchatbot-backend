"""
Authentication middleware for the chatbot backend.

This module provides middleware for authenticating API requests using bearer tokens.
"""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from chatbot_backend.config import API_PREFIX
from chatbot_backend.utils import create_error_response, verify_api_key


async def auth_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """
    Authenticate API requests using bearer token.

    Args:
        request: The FastAPI request object.
        call_next: The next middleware or route handler in the chain.

    Returns:
        The response from the next middleware or route handler.
    """
    # Only check authentication for API routes
    if request.url.path.startswith(API_PREFIX):
        is_authenticated = await verify_api_key(request)
        if not is_authenticated:
            return create_error_response(status_code=401, message="Invalid or missing API key")

    return await call_next(request)

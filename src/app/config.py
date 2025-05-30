"""
Configuration settings for the chatbot backend.

This module centralizes all configuration settings, environment variables,
and constants used throughout the application, making it easier to manage
and update configuration values.
"""

import os
from functools import lru_cache

# Load environment variables
# NOTE: The actual loading of .env file is done in app.py to ensure
# variables are loaded at startup


@lru_cache
def get_api_secret() -> str:
    """
    Get the API secret from environment variables.

    Returns:
        The API secret string.
    """
    return os.environ.get("API_SECRET", "secret_key")


# API route configuration
API_PREFIX = "/api"
API_ROUTES = [
    "/api/chat",
    "/api/generate_title",
]

# Response format configuration
STREAM_CHUNK_PREFIX = "d:"
STREAM_ERROR_PREFIX = "e:"
STREAM_CHUNK_SUFFIX = "\n\n"
STREAM_DONE_MESSAGE = "[DONE]"

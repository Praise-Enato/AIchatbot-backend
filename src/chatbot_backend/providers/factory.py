"""
Provider factory for the chatbot backend.

This module provides functions to get LLM provider instances
based on configuration.
"""

import os

from chatbot_backend.providers.base import LLMProvider
from chatbot_backend.providers.openai import OpenAIProvider

# Global provider cache
_providers: dict[str, LLMProvider] = {}


def get_provider(provider_name: str | None = None) -> LLMProvider:
    """
    Get an LLM provider instance.

    Args:
        provider_name: The name of the provider to use.
                       If None, uses the PROVIDER_NAME env var or defaults to "openai".

    Returns:
        An instance of the requested LLM provider.

    Raises:
        ValueError: If the requested provider is not supported.
    """
    # Determine which provider to use
    if provider_name is None:
        provider_name = os.environ.get("PROVIDER_NAME", "openai")

    # Use cached provider if available
    if provider_name in _providers:
        return _providers[provider_name]

    # Create a new provider instance
    if provider_name.lower() == "openai":
        provider = OpenAIProvider()
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")

    # Cache the provider
    _providers[provider_name] = provider

    return provider


# Pre-initialize the default provider
default_provider = get_provider()

"""
Base provider interface for the chatbot backend.

This module defines the interface that all LLM providers must implement
to be compatible with the chatbot backend.
"""

from collections.abc import Iterator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """
    Protocol defining the interface for LLM providers.

    Any LLM provider implementation must satisfy this interface to be
    compatible with the chatbot backend.
    """

    def get_client(self) -> Any:
        """
        Get a client for the LLM provider.

        Returns:
            A client object for the provider's API.
        """
        ...

    def format_messages_from_request(self, request: Any) -> list[dict[str, Any]]:
        """
        Format messages from the request for the provider's API.

        Args:
            request: The request object containing messages and other data.

        Returns:
            A list of formatted messages compatible with the provider's API.
        """
        ...

    def stream_chat_response(
        self,
        messages: list[dict[str, Any]],
        system_message: str | None = None,
        model: str | None = None,
        tool_definitions: list[dict[str, Any]] | None = None,
    ) -> Iterator[str | dict[str, Any]]:
        """
        Stream a chat response from the provider.

        Args:
            messages: The formatted messages.
            system_message: Optional system message to prepend.
            model: The model to use.
            tool_definitions: Optional tool definitions.

        Yields:
            Text chunks from the provider's API, or dictionaries with usage information.
            Text chunks are returned as strings.
            Usage information is returned as a dictionary with the following format:
            {"usage": {"promptTokens": int, "completionTokens": int}}
        """
        ...

    def get_response(
        self,
        system_message: str,
        user_message: str,
        model: str | None = None,
    ) -> str:
        """
        Get a complete response from the provider for a single message.

        Args:
            system_message: The system message providing context.
            user_message: The user message to respond to.
            model: The model to use.

        Returns:
            The complete response text.
        """
        ...

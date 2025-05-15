"""
OpenAI provider implementation for the chatbot backend.

This module provides the OpenAI implementation of the LLM provider interface
and all OpenAI-specific configuration.
"""

import os
from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from openai import OpenAI

# OpenAI-specific configuration
DEFAULT_MODEL = "gpt-4o-mini"


@lru_cache
def get_openai_api_key() -> str:
    """
    Get the OpenAI API key from environment variables.

    Returns:
        The OpenAI API key.
    """
    return os.environ.get("OPENAI_API_KEY", "")


class OpenAIProvider:
    """OpenAI implementation of the LLM provider interface."""

    def get_client(self) -> OpenAI:
        """
        Get an OpenAI client instance.

        Returns:
            An OpenAI client configured with the API key.
        """
        return OpenAI(
            api_key=get_openai_api_key(),
        )

    def format_messages_from_request(self, request: Any) -> list[dict[str, Any]]:
        """
        Format messages from the request for the OpenAI API.

        Args:
            request: The request object containing messages and other data.

        Returns:
            A list of formatted messages compatible with the OpenAI API.
        """
        formatted_messages = []

        # Add system message if provided
        if request.system is not None:
            formatted_messages.append({"role": "system", "content": request.system})

        # Add the messages from the request
        for message in request.messages:
            formatted_messages.append({"role": message.role, "content": message.content})

        return formatted_messages

    def stream_chat_response(
        self,
        messages: list[dict],
        system_message: str | None = None,
        model: str | None = None,
        tool_definitions: list[dict[str, Any]] | None = None,
    ) -> Iterator[str]:
        """
        Stream a chat response from OpenAI.

        Args:
            messages: The formatted messages.
            system_message: Optional system message to prepend.
            model: Optional model to use, defaults to DEFAULT_MODEL.
            tool_definitions: Optional tool definitions.

        Yields:
            Text chunks from the OpenAI response.
        """
        # Get a client instance
        client = self.get_client()

        if not tool_definitions:
            tool_definitions = []
        if model is None:
            model = DEFAULT_MODEL

        # Prepend system message if provided
        if system_message:
            # Check if there's already a system message at the beginning
            has_system_message = False
            if messages and messages[0].get("role") == "system":
                has_system_message = True

            # Only add system message if there isn't one already
            if not has_system_message:
                system_msg = {"role": "system", "content": system_message}
                messages = [system_msg, *messages]

        # Create a streaming chat completion
        # Note: We use Any for types with the OpenAI API to keep code simple
        stream = client.chat.completions.create(  # type: ignore
            messages=messages,  # type: ignore
            model=model,
            stream=True,
            tools=tool_definitions,
            tool_choice="auto" if tool_definitions else "none",
        )

        # Process each chunk in the stream
        for chunk in stream:
            # Check each choice in the response
            for choice in chunk.choices:
                # Skip if this choice is finished
                if choice.finish_reason == "stop":
                    continue
                # Extract the content if available
                if choice.delta.content:
                    yield choice.delta.content

    def get_response(
        self,
        system_message: str,
        user_message: str,
        model: str | None = None,
    ) -> str:
        """
        Get a complete response from OpenAI for a single message.

        Args:
            system_message: The system message providing context.
            user_message: The user message to respond to.
            model: Optional model to use, defaults to DEFAULT_MODEL.

        Returns:
            The complete response text.
        """
        client = self.get_client()
        if model is None:
            model = DEFAULT_MODEL

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

        # Create a non-streaming chat completion
        # Note: We use simple type handling for OpenAI API for readability
        response = client.chat.completions.create(  # type: ignore
            messages=messages,  # type: ignore
            model=model,
            stream=False,
        )

        # Extract and return the message content
        return response.choices[0].message.content or ""  # type: ignore

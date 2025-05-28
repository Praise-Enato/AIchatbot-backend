"""
Test provider for predictable responses.

This provider handles specific test prompts with predetermined responses,
useful for frontend testing and development.
"""

from collections.abc import Generator
from typing import Any

from chatbot_backend.custom_logger import get_logger
from chatbot_backend.models.chat import ChatRequest

# Configure logging
logger = get_logger("test_provider")

# Test prompts mapping
TEST_PROMPTS: dict[str, dict[str, Any]] = {
    "Test prompt 1": {
        "title": "Test title 1",
        "chat_tokens": ["Test ", "Response ", "1"],
    },
    "Test prompt 2": {
        "title": "Test title 2",
        "chat_tokens": ["Test ", "Response ", "2"],
    },
}


class TestProvider:
    """Test provider for predictable responses."""

    def format_messages_from_request(self, request: ChatRequest) -> list[dict[str, str]]:
        """
        Format messages from chat request into provider format.

        This method exists for compatibility but is not used by the test provider.
        """
        messages = []
        for message in request.messages:
            role = message.role
            content = " ".join(part.text for part in message.parts if part.type == "text")
            messages.append({"role": role, "content": content})
        return messages

    def get_response(self, system_message: str, user_message: str) -> str:  # noqa ARG002
        """
        Get a non-streaming response for test prompts.

        Used for title generation.
        """
        if user_message in TEST_PROMPTS:
            response = TEST_PROMPTS[user_message]["title"]
            logger.info(f"Test provider returning title: {response} for prompt: {user_message}")
            return response

        # This shouldn't happen if the provider is used correctly
        logger.error(f"Test provider called with non-test prompt: {user_message}")
        return "Test Provider Error"

    def stream_chat_response(
        self,
        messages: list[dict[str, str]],
        system_message: str | None = None,  # noqa ARG002
    ) -> Generator[str | dict[str, Any], None, None]:
        """
        Stream a chat response with 100ms delays between tokens.
        """
        # Get the last user message
        last_user_message = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break

        if last_user_message and last_user_message in TEST_PROMPTS:
            tokens = TEST_PROMPTS[last_user_message]["chat_tokens"]
            logger.info(f"Test provider streaming response for prompt: {last_user_message}")

            # Stream tokens with delay
            for token in tokens:
                yield token
                # Sleep for 100ms (this works because FastAPI handles sync generators)
                import time

                time.sleep(0.1)

            # Yield usage data
            yield {"usage": {"promptTokens": 3, "completionTokens": 3}}
        else:
            # This shouldn't happen if the provider is used correctly
            logger.error(f"Test provider called with non-test prompt: {last_user_message}")
            yield "Test Provider Error"


# Create a singleton instance
test_provider = TestProvider()

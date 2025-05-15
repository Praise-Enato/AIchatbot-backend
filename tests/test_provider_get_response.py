"""
Tests for the get_response method in the LLM provider.
"""

import pytest

from chatbot_backend.providers.factory import default_provider


@pytest.mark.slow
def test_get_response():
    """Test get_response method (slow test - makes actual API call)."""
    system_message = "You are a helpful assistant."
    user_message = "What is the capital of France? Answer in one word only."

    response = default_provider.get_response(system_message, user_message)

    # Check that the response contains "Paris" since we can't predict exact format
    assert "Paris" in response, f"Expected Paris in response, got: {response}"

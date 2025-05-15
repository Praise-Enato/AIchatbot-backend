"""
Title generation data models.

This module contains models for the title generation endpoint.
"""

from pydantic import BaseModel


class TextMessage(BaseModel):
    """Text message model."""

    text: str
    type: str = "text"


class GenerateTitleRequest(BaseModel):
    """Request model for the generate_title endpoint."""

    message: TextMessage | str

    def get_message_text(self) -> str:
        """Get the text of the message."""
        if isinstance(self.message, str):
            return self.message
        return self.message.text

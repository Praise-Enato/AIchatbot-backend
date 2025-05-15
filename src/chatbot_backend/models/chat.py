"""
Chat-related data models.

This module contains models for chat messages and requests.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Message model for the chat request format."""

    role: Literal["user", "assistant", "system"]
    content: str
    id: str | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""

    messages: list[Message]
    system: str | None = None
    user_id: str = Field(alias="userId")
    user_type: str = Field(alias="userType")
    chat_id: str = Field(alias="chatId")

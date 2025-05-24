"""
Chat-related data models.

This module contains models for chat messages and requests.
"""

from typing import Any, Literal

from pydantic import Field

from chatbot_backend.models.common import SnakeOrAliasModel


class Chat(SnakeOrAliasModel):
    """Chat model representing a chat entity in the database."""

    chat_id: str = Field(alias="chatId")
    user_id: str = Field(alias="userId")
    chat_created_at: str = Field(alias="chatCreatedAt")
    title: str = Field(alias="title")
    visibility: str = Field(alias="visibility")


class Message(SnakeOrAliasModel):
    """Message model representing a message entity in the database."""

    chat_id: str = Field(alias="chatId")
    created_at: str = Field(alias="createdAt")
    role: Literal["user", "assistant"] = Field(alias="role")
    parts: list[Any] = Field(alias="parts")
    attachments: list[Any] = Field(alias="attachments")
    message_id: str = Field(alias="messageId")


class Vote(SnakeOrAliasModel):
    """Vote model representing a vote entity in the database."""

    chat_id: str = Field(alias="chatId")
    message_id: str = Field(alias="messageId")
    is_upvoted: bool = Field(alias="isUpvoted")


class Stream(SnakeOrAliasModel):
    """Stream model representing a stream entity in the database."""

    chat_id: str = Field(alias="chatId")
    stream_id: str = Field(alias="streamId")
    created_at: str = Field(alias="createdAt")


#
# Request and response models for API endpoints
#


class WireMessage(SnakeOrAliasModel):
    """Wire message model for the chat request format."""

    role: Literal["user", "assistant", "system"] = Field(alias="role")  # TODO: remove system
    content: str = Field(alias="content")
    id: str | None = Field(default=None, alias="id")
    created_at: str | None = Field(default=None, alias="createdAt")


class ChatRequest(SnakeOrAliasModel):
    """Request model for the chat endpoint."""

    messages: list[WireMessage] = Field(alias="messages")
    user_id: str = Field(alias="userId")
    chat_id: str = Field(alias="chatId")


class CreateChatRequest(SnakeOrAliasModel):
    """Request model for creating a new chat."""

    chat_id: str = Field(alias="chatId")
    user_id: str = Field(alias="userId")
    title: str = Field(alias="title")
    visibility: str = Field(alias="visibility")


class SaveMessagesRequest(SnakeOrAliasModel):
    """Request model for saving messages to a chat."""

    user_id: str = Field(alias="userId")
    messages: list[Message] = Field(alias="messages")


class VoteMessageRequest(SnakeOrAliasModel):
    """Request model for voting on a message."""

    vote_type: str = Field(alias="voteType")  # 'up' or 'down'


class CreateStreamRequest(SnakeOrAliasModel):
    """Request model for creating a stream ID."""

    stream_id: str = Field(alias="streamId")


class UpdateChatVisibilityRequest(SnakeOrAliasModel):
    """Request model for updating chat visibility."""

    visibility: str = Field(alias="visibility")


class StreamIdsResponse(SnakeOrAliasModel):
    """Response model for stream IDs list."""

    stream_ids: list[str] = Field(default_factory=list, alias="streamIds")


class ChatListResponse(SnakeOrAliasModel):
    """Response model for paginated chat list."""

    chats: list[Chat] = Field(alias="chats")
    has_more: bool = Field(default=False, alias="hasMore")


class MessageCountResponse(SnakeOrAliasModel):
    """Response model for message count."""

    count: int = Field(alias="count")

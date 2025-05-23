"""
Chat-related data models.

This module contains models for chat messages and requests.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class WireMessage(BaseModel):
    """Wire message model for the chat request format."""

    role: Literal["user", "assistant", "system"]  # TODO: remove system
    content: str
    id: str | None = None
    created_at: str | None = Field(default=None, alias="createdAt")


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""

    messages: list[WireMessage]
    system: str | None = None  # TODO: remove this
    user_id: str = Field(alias="userId")
    user_type: str = Field(alias="userType")  # TODO: remove this
    chat_id: str = Field(alias="chatId")


class Chat(BaseModel):
    """Chat model representing a chat entity in the database."""

    chat_id: str = Field(alias="ChatId")
    user_id: str = Field(alias="UserId")
    chat_created_at: str = Field(alias="ChatCreatedAt")
    title: str = Field(alias="Title")
    visibility: str = Field(alias="Visibility")

    model_config = ConfigDict(populate_by_name=True)


class Message(BaseModel):
    """Message model representing a message entity in the database."""

    chat_id: str = Field(alias="ChatId")
    created_at: str = Field(alias="CreatedAt")
    role: Literal["user", "assistant", "system"] = Field(alias="Role")
    parts: list[Any] = Field(alias="Parts")
    attachments: list[Any] = Field(alias="Attachments")
    message_id: str = Field(alias="MessageId")

    model_config = ConfigDict(populate_by_name=True)


class Vote(BaseModel):
    """Vote model representing a vote entity in the database."""

    chat_id: str = Field(alias="ChatId")
    message_id: str = Field(alias="MessageId")
    is_upvoted: bool = Field(alias="IsUpvoted")

    model_config = ConfigDict(populate_by_name=True)


class Stream(BaseModel):
    """Stream model representing a stream entity in the database."""

    chat_id: str = Field(alias="ChatId")
    created_at: str = Field(alias="CreatedAt")
    stream_id: str = Field(alias="StreamId")

    model_config = ConfigDict(populate_by_name=True)


class ChatListResponse(BaseModel):
    """Response model for paginated chat list."""

    chats: list[Chat]
    has_more: bool


# Request models for API endpoints


class CreateUserRequest(BaseModel):
    """Request model for creating a regular user."""

    email: str
    password: str


class CreateOAuthUserRequest(BaseModel):
    """Request model for creating a user via OAuth."""

    email: str | None = None
    provider: str
    provider_account_id: str


class CreateChatRequest(BaseModel):
    """Request model for creating a new chat."""

    chat_id: str
    user_id: str
    title: str
    visibility: str


class SaveMessagesRequest(BaseModel):
    """Request model for saving messages to a chat."""

    user_id: str
    messages: list[Message]


class VoteMessageRequest(BaseModel):
    """Request model for voting on a message."""

    vote_type: str  # 'up' or 'down'


class CreateStreamRequest(BaseModel):
    """Request model for creating a stream ID."""

    stream_id: str


class UpdateChatVisibilityRequest(BaseModel):
    """Request model for updating chat visibility."""

    visibility: str


class MessageCountResponse(BaseModel):
    """Response model for message count."""

    count: int


class StreamIdsResponse(BaseModel):
    """Response model for stream IDs list."""

    stream_ids: list[str]

from pydantic import BaseModel, Field


class ClientAttachment(BaseModel):
    name: str
    content_type: str = Field(alias="contentType")
    url: str


class ToolInvocation(BaseModel):
    tool_call_id: str = Field(alias="toolCallId")
    tool_name: str = Field(alias="toolName")
    args: dict
    result: dict


class ClientMessage(BaseModel):
    role: str
    content: str
    experimental_attachments: list[ClientAttachment] | None = Field(default=None, alias="experimentalAttachments")
    tool_invocations: list[ToolInvocation] | None = Field(default=None, alias="toolInvocations")


class ChatRequest(BaseModel):
    messages: list[ClientMessage]

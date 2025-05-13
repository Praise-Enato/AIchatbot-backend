import json
import os
from collections.abc import Callable, Iterator
from typing import Any

from openai import OpenAI

from chatbot_backend.models import ClientMessage


def get_client() -> Any:
    return OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )


def convert_messages(messages: list[ClientMessage]) -> list[dict]:
    openai_messages: list[dict[str, Any]] = []

    for message in messages:
        parts: list[dict[str, Any]] = []

        parts.append({"type": "text", "text": message.content})

        if message.experimental_attachments:
            for attachment in message.experimental_attachments:
                if attachment.content_type.startswith("image"):
                    parts.append({"type": "image_url", "image_url": {"url": attachment.url}})

                elif attachment.content_type.startswith("text"):
                    parts.append({"type": "text", "text": attachment.url})

        if message.tool_invocations:
            tool_calls = [
                {
                    "id": tool_invocation.tool_call_id,
                    "type": "function",
                    "function": {"name": tool_invocation.tool_name, "arguments": json.dumps(tool_invocation.args)},
                }
                for tool_invocation in message.tool_invocations
            ]

            openai_messages.append({"role": "assistant", "tool_calls": tool_calls})

            tool_results = [
                {
                    "role": "tool",
                    "content": json.dumps(tool_invocation.result),
                    "tool_call_id": tool_invocation.tool_call_id,
                }
                for tool_invocation in message.tool_invocations
            ]

            openai_messages.extend(tool_results)

            continue

        openai_messages.append({"role": message.role, "content": parts})

    return openai_messages


def stream_response(
    client: OpenAI,
    messages: list[dict],
    protocol: str = "data",
    tool_definitions: list[dict[str, Any]] | None = None,
    tool_functions: list[dict[str, Callable]] | None = None,
) -> Iterator[str]:
    if not tool_definitions:
        tool_definitions = []

    if not tool_functions:
        tool_functions = []

    # Type ignore for OpenAI client SDK - the types are correct at runtime
    stream = client.chat.completions.create(  # type: ignore
        messages=messages,
        model="gpt-4o-mini",
        stream=True,
        tools=tool_definitions,
        tool_choice="auto",
    )

    # When protocol is set to "text", you will send a stream of plain text chunks
    # https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#text-stream-protocol

    if protocol == "text":
        for chunk in stream:
            for choice in chunk.choices:
                if choice.finish_reason == "stop":
                    break
                else:
                    yield f"{choice.delta.content}"

    # When protocol is set to "data", you will send a stream data part chunks
    # https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol

    elif protocol == "data":
        draft_tool_calls: list[dict[str, Any]] = []
        draft_tool_calls_index: int = -1

        for chunk in stream:
            for choice in chunk.choices:
                if choice.finish_reason == "stop":
                    continue

                elif choice.finish_reason == "tool_calls":
                    for tool_call in draft_tool_calls:
                        yield '9:{{"toolCallId":"{id}","toolName":"{name}","args":{args}}}\n'.format(
                            id=tool_call["id"], name=tool_call["name"], args=tool_call["arguments"]
                        )

                    for tool_call in draft_tool_calls:
                        tool_result = tool_functions[tool_call["name"]](**json.loads(tool_call["arguments"]))

                        yield 'a:{{"toolCallId":"{id}","toolName":"{name}","args":{args},"result":{result}}}\n'.format(
                            id=tool_call["id"],
                            name=tool_call["name"],
                            args=tool_call["arguments"],
                            result=json.dumps(tool_result),
                        )

                elif choice.delta.tool_calls:
                    for tool_call in choice.delta.tool_calls:
                        id = tool_call.id  # type: ignore
                        name = tool_call.function.name  # type: ignore
                        arguments = tool_call.function.arguments  # type: ignore

                        if id is not None:
                            draft_tool_calls_index += 1
                            draft_tool_calls.append({"id": id, "name": name, "arguments": ""})

                        else:
                            draft_tool_calls[draft_tool_calls_index]["arguments"] += arguments

                else:
                    yield f"0:{json.dumps(choice.delta.content)}\n"

            if chunk.choices == []:
                usage = chunk.usage
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens

                yield 'd:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion}}}}}\n'.format(  # noqa: E501
                    reason="tool-calls" if len(draft_tool_calls) > 0 else "stop",
                    prompt=prompt_tokens,
                    completion=completion_tokens,
                )

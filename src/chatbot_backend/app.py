from collections.abc import Awaitable, Callable

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import StreamingResponse
from mangum import Mangum
from pydantic import BaseModel

from chatbot_backend.custom_logger import get_logger
from chatbot_backend.models import ChatRequest
from chatbot_backend.providers.openai import convert_messages, get_client, stream_response

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = get_logger("app")


class ResponseModel(BaseModel):
    """Response model for hello/world endpoints."""

    input: str
    output: str


app = FastAPI(
    title="Chatbot Backend",
    description="Example AI chatbot",
    version="0.1.0",
)

client = get_client()

# Example of a simple endpoint


@app.get("/hello", response_model=ResponseModel)
async def hello(request: Request) -> ResponseModel:
    """Hello endpoint that returns a simple response."""
    logger.info("Hello", extra={"path": request.url.path, "method": request.method})
    return ResponseModel(input="hello", output="world")


# Example of a simple middleware


# Simple middleware to log requests
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Log basic information about requests and responses."""
    logger.info("middleware start", extra={"path": request.url.path, "method": request.method})

    response = await call_next(request)

    logger.info("middleware end", extra={"status_code": response.status_code})
    return response


# Streaming chat endpoint


@app.post("/api/chat")
async def handle_chat_data(request: ChatRequest, protocol: str = Query("data")) -> StreamingResponse:
    messages = request.messages
    provider_messages = convert_messages(messages)

    response = StreamingResponse(stream_response(client, provider_messages, protocol))
    response.headers["x-vercel-ai-data-stream"] = "v1"
    return response


# AWS Lambda handler - integrates FastAPI with AWS Lambda
handler = Mangum(app)


# For local development only
if __name__ == "__main__":
    import uvicorn  # type: ignore[import]

    uvicorn.run(app, host="0.0.0.0", port=8000)

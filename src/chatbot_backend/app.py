import logging
import os
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from mangum import Mangum
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Check if running in AWS Lambda environment
in_lambda = "AWS_LAMBDA_FUNCTION_NAME" in os.environ

# Setup console handler for local development
if not in_lambda:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class ResponseModel(BaseModel):
    """Response model for hello/world endpoints."""

    input: str
    output: str


app = FastAPI(
    title="Chatbot Backend",
    description="Example AI chatbot",
    version="0.1.0",
)


@app.get("/hello", response_model=ResponseModel)
async def hello(request: Request) -> ResponseModel:
    """Hello endpoint that returns a simple response."""
    logger.info("Hello", extra={"path": request.url.path, "method": request.method})
    return ResponseModel(input="hello", output="world")


@app.get("/world", response_model=ResponseModel)
async def world(request: Request) -> ResponseModel:
    """World endpoint that returns a simple response."""
    logger.info("World", extra={"path": request.url.path, "method": request.method})
    return ResponseModel(input="world", output="hello")


# Simple middleware to log requests
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Log basic information about requests and responses."""
    logger.info("middleware", extra={"path": request.url.path, "method": request.method})

    response = await call_next(request)

    logger.info(f"Response status code: {response.status_code}")
    return response


# AWS Lambda handler - integrates FastAPI with AWS Lambda
handler = Mangum(app)


# For local development only
if __name__ == "__main__":
    import uvicorn  # type: ignore[import]

    uvicorn.run(app, host="0.0.0.0", port=8000)

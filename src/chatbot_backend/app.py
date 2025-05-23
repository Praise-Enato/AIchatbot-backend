"""
Main application module for the chatbot backend.

This module initializes the FastAPI application, configures middleware,
and includes all routes.
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from mangum import Mangum

from chatbot_backend.custom_logger import get_logger
from chatbot_backend.middleware.auth import auth_middleware
from chatbot_backend.middleware.logging import log_requests
from chatbot_backend.routes import chat, health, title, user

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = get_logger("app")

# Create FastAPI application
app = FastAPI(
    title="Chatbot Backend",
    description="Example AI chatbot",
    version="0.1.0",
)

# Register middleware
app.middleware("http")(auth_middleware)
app.middleware("http")(log_requests)

# Include routers
app.include_router(chat.router)
app.include_router(title.router)
app.include_router(user.router)
app.include_router(health.router)

# AWS Lambda handler - integrates FastAPI with AWS Lambda
handler = Mangum(app)

# For local development only
if __name__ == "__main__":
    import uvicorn  # type: ignore[import]

    uvicorn.run(app, host="0.0.0.0", port=8000)

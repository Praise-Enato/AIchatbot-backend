"""
Main application module for the chatbot backend.

This module initializes the FastAPI application, configures middleware,
and includes all routes.
"""

import os

import boto3
from dotenv import load_dotenv

# Initialize secrets before any other imports that might use environment variables
if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
    # Running in Lambda - load secrets from SSM Parameter Store
    import concurrent.futures

    ssm = boto3.client("ssm")

    def get_parameter(name: str) -> str:
        """Get a parameter from SSM Parameter Store."""
        response = ssm.get_parameter(Name=name, WithDecryption=True)
        return response["Parameter"]["Value"]

    # Load both secrets in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_api_secret = executor.submit(get_parameter, "/chatbot/api-secret")
        future_openai_key = executor.submit(get_parameter, "/chatbot/openai-api-key")

        # Get results
        os.environ["API_SECRET"] = future_api_secret.result()
        os.environ["OPENAI_API_KEY"] = future_openai_key.result()
else:
    # Running locally - load from .env file
    load_dotenv()

# Now import everything else - environment variables are ready
from fastapi import FastAPI
from mangum import Mangum

from chatbot_backend.custom_logger import get_logger
from chatbot_backend.middleware.auth import auth_middleware
from chatbot_backend.routes import chat, health, title, user

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
# app.middleware("http")(log_requests)

# Include routers
app.include_router(chat.router)
app.include_router(title.router)
app.include_router(user.router)
app.include_router(health.router)

# AWS Lambda handler - integrates FastAPI with AWS Lambda
handler = Mangum(app)

"""
Local development entry point for the chatbot backend.

This module loads environment variables and starts the FastAPI server
for local development. In production (Lambda), the handler in app.py
is used directly without loading .env files.
"""

from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# Import the app after loading env vars
from chatbot_backend.app import app  # noqa: E402

# __all__ clarifies that the app is exported for uvicorn to use
__all__ = ["app"]

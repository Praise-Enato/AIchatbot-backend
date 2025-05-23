"""
Pytest configuration file.

This file contains shared fixtures and setup for all tests.
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file before running tests
load_dotenv()

# Set test environment variables if not already set
os.environ.setdefault("USERS_TABLE", "test-users-table")
os.environ.setdefault("CHATS_TABLE", "test-chats-table")
os.environ.setdefault("API_KEY", "test-api-key-for-local-development")

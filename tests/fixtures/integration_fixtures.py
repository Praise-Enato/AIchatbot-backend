"""
Integration test fixtures for FastAPI testing with DynamoDB Local.
"""

import os

import boto3
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from chatbot_backend.app import app

# Load environment variables for all integration tests
load_dotenv()


@pytest.fixture
def auth_headers():
    """Get authentication headers for API requests."""
    api_secret = os.environ["API_SECRET"]
    return {"Authorization": f"Bearer {api_secret}"}


@pytest.fixture(autouse=True)
def clean_tables():
    """Clean all items from DynamoDB tables before each test."""

    def clean_all_tables():
        try:
            # Create local DynamoDB resource for cleaning
            resource = boto3.resource(
                "dynamodb",
                endpoint_url="http://localhost:8000",
            )

            # Get tables
            users_table = resource.Table("Users")
            chats_table = resource.Table("Chats")

            # Scan and delete all items from Users table
            response = users_table.scan()
            for item in response["Items"]:
                users_table.delete_item(Key={"UserId": item["UserId"]})

            # Scan and delete all items from Chats table
            response = chats_table.scan()
            for item in response["Items"]:
                chats_table.delete_item(Key={"ChatId": item["ChatId"], "SK": item["SK"]})
        except Exception as e:
            print(f"Warning: Could not clean tables: {e}")

    # Clean before test
    clean_all_tables()

    yield

    # Clean after test
    clean_all_tables()


@pytest.fixture
def test_client():
    """
    Create a FastAPI test client.

    Note: DynamoDB Local lifecycle is managed by the Makefile test-all target.
    The TESTING_MODE environment variable is set by the Makefile.
    """
    return TestClient(app)

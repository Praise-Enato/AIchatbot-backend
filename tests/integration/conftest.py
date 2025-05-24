"""
Shared configuration and fixtures for integration tests.
"""

import uuid
from datetime import UTC, datetime

import pytest

from tests.fixtures.integration_fixtures import (
    auth_headers,
    test_client,
)

# Import all fixtures to make them available
# Note: clean_tables is autouse=True so doesn't need to be imported
__all__ = [
    "auth_headers",
    "test_client",
    "test_data_generator",
]


@pytest.fixture
def test_data_generator():
    """Helper functions for generating test data."""

    class TestDataGenerator:
        @staticmethod
        def unique_email() -> str:
            """Generate a unique email address for testing."""
            return f"test-{uuid.uuid4()}@example.com"

        @staticmethod
        def unique_id() -> str:
            """Generate a unique ID for testing."""
            return str(uuid.uuid4())

        @staticmethod
        def current_timestamp() -> str:
            """Generate current timestamp in ISO format."""
            return datetime.now(UTC).isoformat().replace("+00:00", "Z")

        @staticmethod
        def test_password_hash() -> str:
            """Generate a test password hash."""

            return "test-password-hash"

        @staticmethod
        def oauth_provider_data() -> dict[str, str]:
            """Generate fake OAuth provider data."""
            return {"provider": "test-provider", "providerAccountId": f"test-account-{uuid.uuid4()}"}

    return TestDataGenerator()

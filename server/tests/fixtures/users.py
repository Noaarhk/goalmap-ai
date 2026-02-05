"""Sample user data for testing."""

from uuid import uuid4


def create_test_user_id() -> str:
    """Generate a random test user ID."""
    return str(uuid4())


# Predefined test users for consistent testing
TEST_USER_1 = {
    "id": "test-user-001",
    "email": "tester1@example.com",
}

TEST_USER_2 = {
    "id": "test-user-002",
    "email": "tester2@example.com",
}

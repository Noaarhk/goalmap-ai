"""Sample conversation and blueprint data for testing."""

from uuid import uuid4

from app.models.conversation import Conversation
from app.schemas.api.chat import BlueprintData, FieldScores


def create_conversation(
    user_id: str | None = None,
    title: str = "Test Conversation",
    conversation_id: str | None = None,
) -> Conversation:
    """Create a Conversation model instance."""
    return Conversation(
        id=conversation_id or str(uuid4()),
        user_id=user_id or str(uuid4()),
        title=title,
    )


def get_sample_blueprint_data() -> dict:
    """Get sample blueprint data as dict (for repository update)."""
    return {
        "goal": "Become a Python Expert",
        "why": "To build amazing AI agents",
        "timeline": "3 months",
        "obstacles": "Limited time, no prior experience",
        "resources": "Official Docs, Online Courses, Mentor",
        "field_scores": {"goal": 80, "why": 70, "timeline": 60},
        "milestones": [
            {"title": "Learn Basics", "description": "Variables, functions, classes"},
            {"title": "Build Projects", "description": "Create 3 real-world projects"},
        ],
    }


def get_sample_blueprint_schema() -> BlueprintData:
    """Get sample blueprint as Pydantic schema."""
    return BlueprintData(
        goal="Become a Python Expert",
        why="To build amazing AI agents",
        timeline="3 months",
        obstacles="Limited time, no prior experience",
        resources="Official Docs, Online Courses, Mentor",
        field_scores=FieldScores(goal=80, why=70, timeline=60),
        milestones=[
            {"title": "Learn Basics", "description": "Variables, functions, classes"},
            {"title": "Build Projects", "description": "Create 3 real-world projects"},
        ],
    )


# Predefined conversations for specific test scenarios
DISCOVERY_CONVERSATION = {
    "title": "Career Change Discovery",
    "blueprint": {
        "goal": "Transition to Backend Engineer",
        "why": "Better career opportunities and passion for system design",
        "timeline": "6 months",
        "obstacles": "Current job demands, limited networking",
        "resources": "4 years frontend experience, online courses budget",
        "field_scores": {"goal": 90, "why": 85, "timeline": 70},
    },
}

INCOMPLETE_CONVERSATION = {
    "title": "Exploring Options",
    "blueprint": {
        "goal": "Learn something new",
        "why": None,
        "timeline": None,
        "obstacles": None,
        "resources": None,
        "field_scores": {"goal": 30},
    },
}

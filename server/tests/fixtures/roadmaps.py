"""Sample roadmap data for testing."""

from uuid import uuid4

from app.schemas.api.roadmaps import GenerateRoadmapRequest
from app.schemas.events.roadmap import ActionNode, GoalNode, Milestone


def create_roadmap_request(
    conversation_id: str | None = None,
    goal: str = "Master Python Programming",
    why: str = "To become a better developer",
) -> GenerateRoadmapRequest:
    """Create a GenerateRoadmapRequest for testing."""
    return GenerateRoadmapRequest(
        conversation_id=conversation_id or str(uuid4()),
        goal=goal,
        why=why,
    )


def create_action_node(
    label: str = "Sample Action",
    details: str = "Action details",
    order: int = 0,
) -> ActionNode:
    """Create an ActionNode for testing."""
    return ActionNode(
        id=f"act-{str(uuid4())[:8]}",
        label=label,
        type="action",
        details=details,
        order=order,
    )


def create_milestone(
    label: str = "Sample Milestone",
    actions: list[ActionNode] | None = None,
    order: int = 0,
) -> Milestone:
    """Create a Milestone for testing."""
    if actions is None:
        actions = [create_action_node(f"Action for {label}")]

    return Milestone(
        id=f"ms-{str(uuid4())[:8]}",
        label=label,
        type="milestone",
        actions=actions,
        order=order,
    )


def create_goal_node(
    label: str = "Sample Goal",
    milestones: list[Milestone] | None = None,
    direct_actions: list[ActionNode] | None = None,
) -> GoalNode:
    """Create a GoalNode for testing."""
    if milestones is None:
        milestones = [
            create_milestone("Milestone 1", order=0),
            create_milestone("Milestone 2", order=1),
        ]

    return GoalNode(
        id=f"goal-{str(uuid4())[:8]}",
        label=label,
        type="goal",
        milestones=milestones,
        actions=direct_actions or [],
    )


def get_sample_milestones_data() -> list[dict]:
    """Get milestone data as list of dicts (for repository create_with_nodes)."""
    return [
        {
            "id": str(uuid4()),
            "label": "Learn Fundamentals",
            "type": "milestone",
            "order": 0,
            "actions": [
                {"id": str(uuid4()), "label": "Study Variables", "type": "action"},
                {"id": str(uuid4()), "label": "Practice Functions", "type": "action"},
            ],
        },
        {
            "id": str(uuid4()),
            "label": "Build Projects",
            "type": "milestone",
            "order": 1,
            "actions": [
                {"id": str(uuid4()), "label": "Create CLI Tool", "type": "action"},
                {"id": str(uuid4()), "label": "Build Web App", "type": "action"},
            ],
        },
    ]


# Predefined roadmap structures for specific scenarios
SIMPLE_ROADMAP = {
    "title": "Simple Learning Path",
    "goal": "Learn Python Basics",
    "milestones": [
        {
            "label": "Getting Started",
            "actions": [{"label": "Install Python"}, {"label": "Setup IDE"}],
        }
    ],
}

COMPLEX_ROADMAP = {
    "title": "Full Stack Developer Path",
    "goal": "Become a Full Stack Developer",
    "milestones": [
        {
            "label": "Frontend Mastery",
            "actions": [
                {"label": "Learn HTML/CSS"},
                {"label": "Master JavaScript"},
                {"label": "React Framework"},
            ],
        },
        {
            "label": "Backend Development",
            "actions": [
                {"label": "Python Fundamentals"},
                {"label": "FastAPI Framework"},
                {"label": "Database Design"},
            ],
        },
        {
            "label": "DevOps Basics",
            "actions": [
                {"label": "Docker Containers"},
                {"label": "CI/CD Pipeline"},
            ],
        },
    ],
}

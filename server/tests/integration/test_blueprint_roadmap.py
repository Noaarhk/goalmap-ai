from uuid import uuid4

import pytest
from app.models.conversation import Conversation
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.roadmap_repo import RoadmapRepository
from sqlalchemy import select
from sqlalchemy.orm import selectinload


@pytest.mark.asyncio
async def test_blueprint_persistence_and_roadmap_creation(db_session):
    # 1. Setup Repository
    conv_repo = ConversationRepository(db_session)
    roadmap_repo = RoadmapRepository(db_session)

    # 2. Create Conversation
    user_id = str(uuid4())
    conv = Conversation(user_id=user_id, title="Integration Test Quest")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    # 3. Simulate Discovery Agent Output (Blueprint Data)
    agent_output = {
        "goal": "Become a Python Expert",
        "why": "To build amazing AI agents",
        "timeline": "3 months",
        "obstacles": "Limited time",
        "resources": "Official Docs, Courses",
        "field_scores": {"goal": 5, "why": 5},
    }

    # 4. Update Blueprint
    await conv_repo.update_blueprint(conv.id, agent_output)

    # Refetch to ensure everything is loaded (and avoiding MissingGreenlet on lazy load)
    updated_conv = await conv_repo.get(conv.id)

    # Verify Blueprint Persistence
    assert updated_conv.blueprint is not None
    assert (
        updated_conv.blueprint.end_point == "Become a Python Expert"
    )  # Mapped from 'goal'
    assert updated_conv.blueprint.motivations == [
        "To build amazing AI agents"
    ]  # Mapped from 'why'

    # Verify New Context Fields
    assert updated_conv.blueprint.timeline == "3 months"
    assert updated_conv.blueprint.obstacles == "Limited time"
    assert updated_conv.blueprint.resources == "Official Docs, Courses"

    # Verify Start Point is Clean (Not polluted by context)
    assert updated_conv.blueprint.start_point is None

    # 5. Create Roadmap (Simulating Roadmap Agent)
    # Note: RoadmapRepository.create_with_nodes uses conversation_id for 1:1 link
    roadmap = await roadmap_repo.create_with_nodes(
        user_id=user_id,
        title="Python Mastery Path",
        goal="Become a Python Expert",
        milestones_data=[
            {
                "id": str(uuid4()),
                "label": "Learn Basics",
                "type": "milestone",
                "order": 1,
                "actions": [
                    {"id": str(uuid4()), "label": "Variables", "type": "action"}
                ],
            }
        ],
        conversation_id=conv.id,
    )

    # Verify Roadmap Persistence and 1:1 Link
    assert roadmap.id is not None
    assert roadmap.conversation_id == conv.id
    assert roadmap.title == "Python Mastery Path"

    # Refetch Roadmap to ensure nodes are loaded
    roadmap_fetched = await roadmap_repo.get(roadmap.id)
    assert roadmap_fetched is not None

    # Verify Nodes
    assert len(roadmap_fetched.nodes) > 0

    # Find the milestone node
    milestone_node = next(
        (n for n in roadmap_fetched.nodes if n.label == "Learn Basics"), None
    )
    assert milestone_node is not None
    assert milestone_node.type == "milestone"

    # Optional: Find action node
    action_node = next(
        (n for n in roadmap_fetched.nodes if n.label == "Variables"), None
    )
    assert action_node is not None
    assert action_node.type == "action"

    # Verify Conversation -> Roadmap link
    # Repository.get() currently doesn't eager load roadmap, so we do it explicitly here for verification
    query = (
        select(Conversation)
        .where(Conversation.id == conv.id)
        .options(selectinload(Conversation.roadmap))
    )
    result = await db_session.execute(query)
    conv_with_roadmap = result.scalar_one()

    assert conv_with_roadmap.roadmap is not None
    assert conv_with_roadmap.roadmap.id == roadmap.id

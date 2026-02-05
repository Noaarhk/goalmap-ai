"""
Tests for Roadmap persistence through the service layer.
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from app.models.conversation import Conversation
from app.models.node import NodeType
from app.models.roadmap import Roadmap
from app.schemas.api.roadmaps import GenerateRoadmapRequest
from app.schemas.events.roadmap import ActionNode, GoalNode, Milestone
from app.services.roadmap_service import RoadmapStreamService
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from tests.conftest import TestUnitOfWork


@pytest.mark.asyncio
async def test_roadmap_service_persistence(db_session):
    """Test that RoadmapStreamService correctly persists roadmap with nodes."""
    # 1. Setup
    user_id = str(uuid4())
    conv_id = str(uuid4())

    conv = Conversation(id=conv_id, user_id=user_id, title="Test Conv")
    db_session.add(conv)
    await db_session.commit()

    request = GenerateRoadmapRequest(
        conversation_id=conv_id,
        goal="Service Persistence Test",
        why="Verification",
    )

    # 2. Build GoalNode structure
    action_id = f"act-{str(uuid4())[:8]}"
    ms_id = f"ms-{str(uuid4())[:8]}"

    action_node = ActionNode(
        id=action_id,
        label="Persisted Action",
        type="action",
        details="Should be in DB",
        order=0,
    )

    milestone_node = Milestone(
        id=ms_id,
        label="Persisted Milestone",
        type="milestone",
        actions=[action_node],
        order=0,
    )

    goal_node = GoalNode(
        id=f"goal-{str(uuid4())[:8]}",
        label="Service Goal",
        type="goal",
        milestones=[milestone_node],
        actions=[],
    )

    # 3. Call Service (using shared TestUnitOfWork from conftest)
    uow = TestUnitOfWork(db_session)
    mock_graph_manager = MagicMock()
    service = RoadmapStreamService(uow, mock_graph_manager)

    await service._persist_roadmap(request, goal_node, user_id)

    # 4. Verify persistence
    stmt = (
        select(Roadmap)
        .where(Roadmap.conversation_id == conv_id)
        .options(selectinload(Roadmap.nodes))
    )
    result = await db_session.execute(stmt)
    roadmap = result.scalars().first()

    assert roadmap is not None
    assert roadmap.title == "Service Persistence Test"

    # Verify nodes
    nodes = roadmap.nodes
    milestone = next((n for n in nodes if n.type == NodeType.MILESTONE), None)
    assert milestone is not None
    assert milestone.label == "Persisted Milestone"

    action = next((n for n in nodes if n.type == NodeType.ACTION), None)
    assert action is not None
    assert action.label == "Persisted Action"
    assert action.parent_id == milestone.id

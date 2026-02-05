from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.models.conversation import Conversation
from app.models.node import NodeType
from app.models.roadmap import Roadmap
from app.schemas.roadmap import GenerateRoadmapRequest
from app.services.roadmap_service import RoadmapStreamService
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Mock Responses
SKELETON_RESP = {
    "goal": {
        "label": "Full Flow Goal",
        "details": "Details",
        "milestones": [{"label": "M1", "details": "d1", "actions": []}],
        "actions": [],
    }
}
ACTIONS_RESP = {"actions": [{"label": "A1", "details": "ad1", "is_assumed": False}]}


@pytest.mark.asyncio
async def test_roadmap_full_flow_persistence(db_session):
    # 1. Setup
    user_id = str(uuid4())
    conv_id = str(uuid4())

    # Create conversation for FK
    conv = Conversation(id=conv_id, user_id=user_id, title="Test Conv")
    db_session.add(conv)
    await db_session.commit()

    request = GenerateRoadmapRequest(
        conversation_id=conv_id,
        goal="Full Flow Goal",
        why="Testing",
    )

    # 2. Mock LLM and Session Factory
    # We patch ainvoke to return fake data so graph runs successfully
    # We patch async_session_factory to use our test db_session so checking persistence works

    mock_invoke = AsyncMock()
    # We need to return different things based on call count or input, but simpler:
    # merge keys.
    mock_invoke.return_value = {
        "goal": SKELETON_RESP["goal"],
        "actions": ACTIONS_RESP["actions"],
    }

    # Mock context manager for session
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__.return_value = db_session
    mock_session_ctx.__aexit__.return_value = None

    with patch("langchain_core.runnables.base.RunnableSequence.ainvoke", mock_invoke):
        with patch(
            "app.services.roadmap_service.async_session_factory",
            return_value=mock_session_ctx,
        ):
            # 3. Run Stream
            # Consume the generator
            events = []
            async for event in RoadmapStreamService.stream_roadmap(request, user_id):
                events.append(event)

            # 4. Verify Events (UI side)
            assert len(events) >= 3  # Skeleton, Actions(M1), DirectActions(Goal)

            # 5. Verify Persistence (DB side)
            stmt = (
                select(Roadmap)
                .where(Roadmap.conversation_id == conv_id)
                .options(selectinload(Roadmap.nodes))
            )
            result = await db_session.execute(stmt)
            roadmap = result.scalars().first()

            assert roadmap is not None, "Roadmap should be persisted"
            assert roadmap.goal == "Full Flow Goal"

            assert len(roadmap.nodes) > 0
            milestones = [n for n in roadmap.nodes if n.type == NodeType.MILESTONE]
            actions = [n for n in roadmap.nodes if n.type == NodeType.ACTION]

            assert len(milestones) == 1
            assert milestones[0].label == "M1"

            # Verify Actions saved
            assert len(actions) >= 1
            # Note: direct actions might be 1 (from ACTIONS_RESP applied to Goal Actions logic?)
            # Wait, 'generate_direct_actions' in graph calls chain.
            # Our mock returns 'actions'. So it should generate goal actions too.
            # And 'generate_actions' for M1 also returns 'actions'.
            # So we expect M1 actions + Goal actions.

"""
Integration tests for full Roadmap generation flow with HIL (Human-in-the-Loop).
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.models.conversation import Conversation
from app.models.node import NodeType
from app.models.roadmap import Roadmap
from app.schemas.api.roadmaps import GenerateRoadmapRequest
from app.services.roadmap_service import RoadmapStreamService
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from tests.conftest import TestUnitOfWork

# Mock LLM Responses
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
    """Test full roadmap generation flow with DB persistence."""
    # 1. Setup
    user_id = str(uuid4())
    conv_id = str(uuid4())

    conv = Conversation(id=conv_id, user_id=user_id, title="Test Conv")
    db_session.add(conv)
    await db_session.commit()

    request = GenerateRoadmapRequest(
        conversation_id=conv_id,
        goal="Full Flow Goal",
        why="Testing",
    )

    # 2. Mock LLM
    mock_invoke = AsyncMock()
    mock_invoke.return_value = {
        "goal": SKELETON_RESP["goal"],
        "actions": ACTIONS_RESP["actions"],
    }

    with patch("langchain_core.runnables.base.RunnableSequence.ainvoke", mock_invoke):
        # 3. Setup Service with shared TestUnitOfWork
        uow = TestUnitOfWork(db_session)
        service = RoadmapStreamService(uow)

        # 4. Run Stream
        events = []
        async for event in service.stream_roadmap(request, user_id):
            events.append(event)

        # 5. Verify Events
        assert len(events) >= 2

        skeleton_events = [e for e in events if "roadmap_skeleton" in e]
        assert len(skeleton_events) == 1

        # 6. Verify Persistence
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
        assert len(actions) >= 1


@pytest.mark.asyncio
async def test_roadmap_hil_flow_two_step(db_session):
    """Test HIL flow: skeleton generation (persisted to DB), then actions after approval."""
    # 1. Setup
    user_id = str(uuid4())
    conv_id = str(uuid4())

    conv = Conversation(id=conv_id, user_id=user_id, title="HIL Test Conv")
    db_session.add(conv)
    await db_session.commit()

    request = GenerateRoadmapRequest(
        conversation_id=conv_id,
        goal="HIL Flow Goal",
        why="Testing HIL",
    )

    mock_invoke = AsyncMock()
    mock_invoke.return_value = {
        "goal": {
            "label": "HIL Flow Goal",
            "details": "Details",
            "milestones": [{"label": "M1", "details": "d1", "actions": []}],
            "actions": [],
        },
        "actions": [{"label": "A1", "details": "ad1", "is_assumed": False}],
    }

    with patch("langchain_core.runnables.base.RunnableSequence.ainvoke", mock_invoke):
        uow = TestUnitOfWork(db_session)
        service = RoadmapStreamService(uow)

        # Step 1: Generate skeleton (persisted as DRAFT in DB)
        skeleton_events = []
        roadmap_id = None
        async for event in service.stream_skeleton(request, user_id):
            skeleton_events.append(event)
            if "roadmap_id" in event:
                import json

                data_start = event.find("data: ") + 6
                data = json.loads(event[data_start:].strip())
                roadmap_id = data.get("roadmap_id")

        assert len(skeleton_events) >= 1
        assert roadmap_id is not None

        # Verify skeleton is persisted as DRAFT
        stmt = (
            select(Roadmap)
            .where(Roadmap.id == roadmap_id)
            .options(selectinload(Roadmap.nodes))
        )
        result = await db_session.execute(stmt)
        draft_roadmap = result.scalars().first()
        assert draft_roadmap is not None
        assert draft_roadmap.status.value == "draft"

        # Step 2: Resume and generate actions (loads from DB)
        action_events = []
        async for event in service.stream_actions(roadmap_id, user_id):
            action_events.append(event)

        assert len(action_events) >= 1

        # Verify persistence and activation
        await db_session.expire_all()
        result = await db_session.execute(stmt)
        roadmap = result.scalars().first()

        assert roadmap is not None
        assert roadmap.goal == "HIL Flow Goal"
        assert roadmap.status.value == "active"
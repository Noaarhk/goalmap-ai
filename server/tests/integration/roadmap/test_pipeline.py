"""
Tests for Roadmap Pipeline functions.

Tests the plain async functions for roadmap generation (skeleton & actions).
"""

from unittest.mock import AsyncMock, patch

import pytest
from app.agents.roadmap.pipeline import generate_actions, generate_skeleton
from app.schemas.events.roadmap import GoalNode, Milestone


@pytest.mark.asyncio
async def test_generate_skeleton():
    """Test skeleton generation function returns valid GoalNode structure."""
    context = {
        "goal": "Test Goal",
        "why": "Testing",
        "timeline": "ASAP",
    }

    mock_response = {
        "goal": {
            "label": "Test Goal",
            "details": "Main goal details",
            "milestones": [
                {"label": "Milestone 1", "details": "M1 details", "actions": []},
                {"label": "Milestone 2", "details": "M2 details", "actions": []},
            ],
            "actions": [],
        }
    }

    with patch(
        "langchain_core.runnables.base.RunnableSequence.ainvoke", new_callable=AsyncMock
    ) as mock_invoke:
        mock_invoke.return_value = mock_response

        result = await generate_skeleton(context)

        assert result is not None
        assert result.label == "Test Goal"
        assert len(result.milestones) == 2
        assert result.milestones[0].label == "Milestone 1"
        # Actions should be empty in skeleton
        assert len(result.milestones[0].actions) == 0


@pytest.mark.asyncio
async def test_generate_actions():
    """Test action generation populates milestones with actions."""
    goal_node = GoalNode(
        id="goal-1",
        label="Test Goal",
        type="goal",
        milestones=[
            Milestone(id="ms-1", label="Milestone 1", type="milestone", actions=[]),
            Milestone(id="ms-2", label="Milestone 2", type="milestone", actions=[]),
        ],
        actions=[],
    )

    context = {"goal": "Test Goal", "why": "Testing"}

    mock_response = {
        "actions": [{"label": "Action 1", "details": "Do it", "is_assumed": False}]
    }

    with patch(
        "langchain_core.runnables.base.RunnableSequence.ainvoke", new_callable=AsyncMock
    ) as mock_invoke:
        mock_invoke.return_value = mock_response

        result = await generate_actions(goal_node, context)

        assert result is not None
        # Each milestone should have actions
        assert len(result.milestones[0].actions) >= 1
        assert result.milestones[0].actions[0].label == "Action 1"
        # Goal should have direct actions
        assert len(result.actions) >= 1


@pytest.mark.asyncio
async def test_full_pipeline_skeleton_then_actions():
    """Test full pipeline: skeleton → actions."""
    context = {
        "goal": "Full Pipeline Goal",
        "why": "Testing full flow",
    }

    skeleton_response = {
        "goal": {
            "label": "Full Pipeline Goal",
            "details": "Main goal",
            "milestones": [
                {"label": "M1", "details": "Details", "actions": []},
            ],
            "actions": [],
        }
    }

    actions_response = {
        "actions": [{"label": "A1", "details": "Action", "is_assumed": False}]
    }

    mock_response = {
        "goal": skeleton_response["goal"],
        "actions": actions_response["actions"],
    }

    with patch(
        "langchain_core.runnables.base.RunnableSequence.ainvoke", new_callable=AsyncMock
    ) as mock_invoke:
        mock_invoke.return_value = mock_response

        # Step 1: Generate skeleton
        skeleton = await generate_skeleton(context)
        assert skeleton is not None
        assert len(skeleton.milestones) == 1
        assert len(skeleton.milestones[0].actions) == 0  # No actions yet

        # Step 2: Generate actions
        final = await generate_actions(skeleton, context)
        assert final is not None
        assert len(final.milestones[0].actions) >= 1  # Now has actions
        assert len(final.actions) >= 1  # Direct actions too

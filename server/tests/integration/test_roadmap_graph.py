from unittest.mock import AsyncMock, patch

import pytest
from app.agents.roadmap.graph import roadmap_graph


@pytest.mark.asyncio
async def test_roadmap_graph_execution():
    # 1. Setup Initial State
    initial_state = {
        "context": {
            "goal": "Graph Test Goal",
            "why": "Testing Flow",
            "timeline": "ASAP",
        },
        "goal_node": None,
    }

    # 2. Mock LLM Responses for each step
    # We need to mock the chain execution inside each node: plan_skeleton, generate_actions, generate_direct_actions
    # Since they all use `chain.ainvoke`, we can patch RunnableSequence.ainvoke

    # We need different responses based on the prompt/input?
    # Or simplified: if the nodes Logic works, they just parse whatever JSON we give.

    # Skeleton Response
    skeleton_resp = {
        "goal": {
            "label": "Graph Test Goal",
            "details": "Main goal",
            "milestones": [
                {"label": "Milestone 1", "details": "M1 details", "actions": []},
                {"label": "Milestone 2", "details": "M2 details", "actions": []},
            ],
            "actions": [],
        }
    }

    # Actions Response (for each milestone)
    actions_resp = {
        "actions": [{"label": "Action 1", "details": "Do it", "is_assumed": False}]
    }

    # Direct Actions Response
    direct_actions_resp = {
        "actions": [
            {"label": "Direct Action 1", "details": "Global", "is_assumed": False}
        ]
    }

    # Side Effect function to return different responses based on input?
    # Or just returning a generic response that satisfies all parsers?
    # The parsers look for specific keys.
    # plan_skeleton looks for "goal"
    # generate_actions looks for "actions"
    # generate_direct_actions looks for "actions"

    # We can merge them into one superset response for simplicity,
    # OR use side_effect to check args (too complex for 'ainvoke' args).
    # Superset approach:
    mock_response = {
        "goal": skeleton_resp["goal"],
        "actions": actions_resp["actions"],  # This works for both action steps
    }

    with patch(
        "langchain_core.runnables.base.RunnableSequence.ainvoke", new_callable=AsyncMock
    ) as mock_invoke:
        mock_invoke.return_value = mock_response

        # 3. Execute Graph
        result = await roadmap_graph.ainvoke(initial_state)

        # 4. Verify Final State
        assert "goal_node" in result
        goal_node = result["goal_node"]
        assert goal_node is not None
        assert goal_node.label == "Graph Test Goal"

        # Check Milestones (Skeleton step)
        assert len(goal_node.milestones) == 2
        assert goal_node.milestones[0].label == "Milestone 1"

        # Check Actions (Actions step)
        # Since we mocked the response, each milestone should have gotten the actions
        # Note: generate_actions iterates over milestones and calls chain for each.
        # Our mock returns actions_resp for each call.
        assert len(goal_node.milestones[0].actions) == 1
        assert goal_node.milestones[0].actions[0].label == "Action 1"

        # Check Direct Actions (Direct Actions step)
        # Note: generate_direct_actions calls chain and expects "actions"
        assert len(goal_node.actions) == 1
        assert goal_node.actions[0].label == "Action 1"  # Same mock response label

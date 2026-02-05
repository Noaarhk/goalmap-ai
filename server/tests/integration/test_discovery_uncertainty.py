from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.agents.discovery.nodes import analyze_turn
from app.agents.discovery.state import DiscoveryState
from app.schemas.api.chat import BlueprintData, FieldScores
from langchain_core.messages import HumanMessage


@pytest.mark.asyncio
async def test_uncertainty_extraction_and_persistence():
    # 1. Setup Initial State
    blueprint = BlueprintData(goal="Learn Python", field_scores=FieldScores(goal=50))

    state: DiscoveryState = {
        "messages": [
            HumanMessage(
                content="I want to learn Python but I'm not sure when to start."
            )
        ],
        "blueprint": blueprint,
        "next": "",
        "user_id": str(uuid4()),
    }

    # 2. Mock LLM/Chain Output
    # We mock the chain.ainvoke to return our expected JSON
    mock_response = {
        "extracted": {"timeline": "Unsure"},
        "scores": {"goal": 60, "timeline": 20},
        "uncertainties": [{"text": "Start date is uncertain", "type": "timeline"}],
    }

    # Patching the chain execution inside analyze_turn
    # Since analyze_turn builds the chain dynamically: chain = prompt | llm | ...
    # We verify the LOGIC, so we can mock the RunnableSequence.ainvoke

    with patch(
        "langchain_core.runnables.base.RunnableSequence.ainvoke", new_callable=AsyncMock
    ) as mock_invoke:
        mock_invoke.return_value = mock_response

        # 3. Execute Node
        result = await analyze_turn(state)

        # 4. Verify Result
        assert "blueprint" in result
        updated_blueprint = result["blueprint"]

        # Verify Uncertainty Persistence
        assert updated_blueprint.uncertainties is not None
        assert len(updated_blueprint.uncertainties) == 1
        assert updated_blueprint.uncertainties[0]["text"] == "Start date is uncertain"
        assert updated_blueprint.uncertainties[0]["type"] == "timeline"

        # Verify Normal Update
        assert updated_blueprint.field_scores.goal == 60
        assert updated_blueprint.field_scores.timeline == 20

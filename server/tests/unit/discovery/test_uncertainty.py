"""
Unit test for discovery agent uncertainty extraction.

This tests the analyze_turn pipeline logic with mocked LLM responses.
No database interaction - pure logic validation.
"""

from unittest.mock import AsyncMock, patch

import pytest
from app.agents.discovery.pipeline import analyze_turn
from app.schemas.api.chat import BlueprintData, FieldScores
from langchain_core.messages import HumanMessage


@pytest.mark.asyncio
async def test_uncertainty_extraction_updates_blueprint():
    """Test that uncertainties are correctly extracted and stored in blueprint."""
    blueprint = BlueprintData(goal="Learn Python", field_scores=FieldScores(goal=50))
    messages = [
        HumanMessage(content="I want to learn Python but I'm not sure when to start.")
    ]

    mock_response = {
        "extracted": {"timeline": "Unsure"},
        "scores": {"goal": 60, "timeline": 20},
        "uncertainties": [{"text": "Start date is uncertain", "type": "timeline"}],
    }

    with patch(
        "langchain_core.runnables.base.RunnableSequence.ainvoke", new_callable=AsyncMock
    ) as mock_invoke:
        mock_invoke.return_value = mock_response

        result = await analyze_turn(messages, blueprint)

        # Verify Uncertainty Persistence
        assert result.uncertainties is not None
        assert len(result.uncertainties) == 1
        assert result.uncertainties[0]["text"] == "Start date is uncertain"
        assert result.uncertainties[0]["type"] == "timeline"

        # Verify Score Update
        assert result.field_scores.goal == 60
        assert result.field_scores.timeline == 20


@pytest.mark.asyncio
async def test_uncertainty_with_multiple_fields():
    """Test handling multiple uncertainties from single turn."""
    blueprint = BlueprintData(goal="Career change", field_scores=FieldScores(goal=40))
    messages = [
        HumanMessage(
            content="I want to change careers but not sure about timeline or obstacles."
        )
    ]

    mock_response = {
        "extracted": {"timeline": "Unknown", "obstacles": "Unclear"},
        "scores": {"goal": 50, "timeline": 15, "obstacles": 10},
        "uncertainties": [
            {"text": "Timeline not defined", "type": "timeline"},
            {"text": "Obstacles unknown", "type": "obstacles"},
        ],
    }

    with patch(
        "langchain_core.runnables.base.RunnableSequence.ainvoke", new_callable=AsyncMock
    ) as mock_invoke:
        mock_invoke.return_value = mock_response

        result = await analyze_turn(messages, blueprint)

        assert len(result.uncertainties) == 2


@pytest.mark.asyncio
async def test_analyze_turn_returns_unchanged_on_failure():
    """Test that blueprint is returned unchanged if analysis fails."""
    blueprint = BlueprintData(goal="Original Goal", field_scores=FieldScores(goal=50))
    messages = [HumanMessage(content="Some message")]

    with patch(
        "langchain_core.runnables.base.RunnableSequence.ainvoke", new_callable=AsyncMock
    ) as mock_invoke:
        mock_invoke.side_effect = Exception("LLM Error")

        result = await analyze_turn(messages, blueprint)

        # Should return original blueprint unchanged
        assert result.goal == "Original Goal"
        assert result.field_scores.goal == 50

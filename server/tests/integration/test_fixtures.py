"""Test seeded fixtures work correctly."""

import pytest


@pytest.mark.asyncio
async def test_seeded_user_id(seeded_user_id):
    """Test that seeded_user_id fixture provides consistent ID."""
    assert seeded_user_id is not None
    assert seeded_user_id == "test-user-001"


@pytest.mark.asyncio
async def test_seeded_conversation(seeded_conversation):
    """Test that seeded_conversation fixture creates conversation with blueprint."""
    assert seeded_conversation is not None
    assert seeded_conversation.title == "Seeded Test Conversation"
    assert seeded_conversation.user_id == "test-user-001"

    # Verify blueprint is attached
    assert seeded_conversation.blueprint is not None
    assert seeded_conversation.blueprint.goal == "Become a Python Expert"
    assert seeded_conversation.blueprint.timeline == "3 months"


@pytest.mark.asyncio
async def test_seeded_roadmap(seeded_roadmap, seeded_conversation):
    """Test that seeded_roadmap fixture creates roadmap with nodes."""
    assert seeded_roadmap is not None
    assert seeded_roadmap.title == "Seeded Test Roadmap"
    assert seeded_roadmap.goal == "Master Python Programming"

    # Verify linked to conversation
    assert seeded_roadmap.conversation_id == seeded_conversation.id

    # Verify nodes exist
    assert len(seeded_roadmap.nodes) > 0

    # Should have 2 milestones with 2 actions each = 6 nodes total
    milestones = [n for n in seeded_roadmap.nodes if n.type.value == "milestone"]
    actions = [n for n in seeded_roadmap.nodes if n.type.value == "action"]

    assert len(milestones) == 2
    assert len(actions) == 4

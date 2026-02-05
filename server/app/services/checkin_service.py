import json
from uuid import UUID

from app.core.uow import AsyncUnitOfWork
from app.models.checkin import CheckIn
from app.models.node import Node
from app.schemas.api.checkins import NodeUpdate
from app.services.gemini import get_llm
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select


CHECKIN_ANALYSIS_PROMPT = """You are a progress analyst for a goal-tracking application. 
Analyze the user's check-in update and determine which tasks/milestones were worked on.

You will receive:
1. The user's check-in text describing what they accomplished
2. A list of nodes (tasks/milestones) from their roadmap

Your job is to:
1. Identify which nodes the user's work relates to
2. Estimate the progress increment (0-100) for each affected node
3. Write a brief log entry for each update

Guidelines:
- Only include nodes that are clearly relevant to the check-in text
- Be conservative with progress estimates (5-25% for small tasks, more for significant work)
- Log entries should be concise but descriptive
- If the user explicitly mentions completing something, you can give higher progress

Return a JSON object with this exact structure:
{
    "updates": [
        {
            "node_id": "uuid-string",
            "progress_delta": 15,
            "log_entry": "Completed initial research phase"
        }
    ]
}

If no nodes match the check-in, return: {"updates": []}
"""


async def analyze_checkin(
    roadmap_id: UUID, user_input: str, uow: AsyncUnitOfWork
) -> tuple[CheckIn, list[NodeUpdate]]:
    """
    Analyze user's check-in text and propose updates to roadmap nodes.
    Returns the created CheckIn record and list of proposed updates.
    """
    async with uow:
        # Get all nodes for this roadmap
        result = await uow.session.execute(
            select(Node).where(Node.roadmap_id == roadmap_id)
        )
        nodes = result.scalars().all()

        if not nodes:
            raise ValueError(f"No nodes found for roadmap {roadmap_id}")

        # Build node context for LLM
        node_context = "\n".join(
            [
                f"- ID: {node.id}, Label: {node.label}, Type: {node.type.value}, Current Progress: {node.progress}%"
                for node in nodes
            ]
        )

        # Call LLM
        llm = get_llm()
        messages = [
            SystemMessage(content=CHECKIN_ANALYSIS_PROMPT),
            HumanMessage(
                content=f"""User's check-in: "{user_input}"

Available nodes:
{node_context}

Analyze and return JSON with updates."""
            ),
        ]

        response = await llm.ainvoke(messages)
        response_text = (
            response.content
            if isinstance(response.content, str)
            else response.content[0].get("text", "{}")
        )

        # Parse response - handle markdown code blocks
        json_str = response_text.strip()
        if json_str.startswith("```"):
            # Remove markdown code block
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1])

        try:
            parsed = json.loads(json_str)
            proposed_updates = parsed.get("updates", [])
        except json.JSONDecodeError:
            proposed_updates = []

        # Create CheckIn record
        checkin = CheckIn(
            roadmap_id=roadmap_id,
            user_input=user_input,
            proposed_updates=proposed_updates,
            status="pending",
        )
        uow.session.add(checkin)
        await uow.commit()
        await uow.session.refresh(checkin)

        # Convert to Pydantic models
        update_models = [
            NodeUpdate(
                node_id=UUID(u["node_id"]),
                progress_delta=u["progress_delta"],
                log_entry=u["log_entry"],
            )
            for u in proposed_updates
        ]

        return checkin, update_models


async def confirm_checkin(
    checkin_id: UUID,
    uow: AsyncUnitOfWork,
    custom_updates: list[NodeUpdate] | None = None,
) -> list[UUID]:
    """
    Confirm and apply the proposed updates from a check-in.
    If custom_updates is provided, use those instead of the original proposed_updates.
    Returns list of updated node IDs.
    """
    async with uow:
        # Get the check-in
        result = await uow.session.execute(
            select(CheckIn).where(CheckIn.id == checkin_id)
        )
        checkin = result.scalar_one_or_none()

        if not checkin:
            raise ValueError(f"CheckIn {checkin_id} not found")

        if checkin.status != "pending":
            raise ValueError(f"CheckIn {checkin_id} is already {checkin.status}")

        # Use custom updates if provided, otherwise use original proposed_updates
        updates_to_apply = (
            [u.model_dump() for u in custom_updates]
            if custom_updates
            else checkin.proposed_updates
        )

        updated_node_ids: list[UUID] = []
        confirmed_updates: list[dict] = []

        for update in updates_to_apply:
            node_id = UUID(str(update["node_id"]))
            progress_delta = update["progress_delta"]

            # Get and update the node
            node_result = await uow.session.execute(
                select(Node).where(Node.id == node_id)
            )
            node = node_result.scalar_one_or_none()

            if node:
                # Clamp progress to 0-100
                old_progress = node.progress
                new_progress = min(100, node.progress + progress_delta)
                node.progress = new_progress
                updated_node_ids.append(node_id)
                confirmed_updates.append(
                    {
                        **update,
                        "node_id": str(node_id),
                        "previous_progress": old_progress,
                        "new_progress": new_progress,
                    }
                )

        # Update check-in status
        checkin.confirmed_updates = confirmed_updates
        checkin.status = "confirmed"

        await uow.commit()

        return updated_node_ids


async def reject_checkin(checkin_id: UUID, uow: AsyncUnitOfWork) -> None:
    """Reject a pending check-in without applying updates."""
    async with uow:
        result = await uow.session.execute(
            select(CheckIn).where(CheckIn.id == checkin_id)
        )
        checkin = result.scalar_one_or_none()

        if not checkin:
            raise ValueError(f"CheckIn {checkin_id} not found")

        if checkin.status != "pending":
            raise ValueError(f"CheckIn {checkin_id} is already {checkin.status}")

        checkin.status = "rejected"
        await uow.commit()

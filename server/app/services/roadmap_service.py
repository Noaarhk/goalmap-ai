"""
Roadmap Streaming Service (DB-backed, no in-memory cache)

Supports 2-step generation flow with HIL:
1. stream_skeleton() - Generates milestone structure, persists as DRAFT
2. stream_actions()  - Loads from DB, generates actions, sets ACTIVE
"""

import logging
from typing import AsyncGenerator
from uuid import UUID

from app.agents.roadmap.pipeline import generate_actions, generate_skeleton
from app.core.uow import AsyncUnitOfWork
from app.models.node import NodeType
from app.schemas.api.roadmaps import GenerateRoadmapRequest, ModifiedMilestone
from app.schemas.events.base import ErrorEventData
from app.schemas.events.roadmap import (
    GoalNode,
    Milestone,
    RoadmapActionsEvent,
    RoadmapCompleteEvent,
    RoadmapSkeletonEvent,
)

logger = logging.getLogger(__name__)


class RoadmapStreamService:
    """Service for streaming Roadmap generation with HIL support."""

    def __init__(self, uow: AsyncUnitOfWork):
        self.uow = uow

    # ------------------------------------------------------------------
    # HIL Step 1: Generate skeleton → persist to DB as DRAFT
    # ------------------------------------------------------------------

    async def stream_skeleton(
        self,
        request: GenerateRoadmapRequest,
        user_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        Step 1: Generate roadmap skeleton (milestones only).

        Persists Roadmap(DRAFT) + Goal Node + Milestones to DB.
        Returns roadmap_id for Step 2.
        """
        logger.info(f"[Skeleton] Starting for goal='{request.goal}'")

        context = {
            "goal": request.goal,
            "why": request.why,
            "timeline": request.timeline,
            "obstacles": request.obstacles,
            "resources": request.resources,
        }

        try:
            # Generate skeleton via LLM
            goal_node = await generate_skeleton(context)

            if not goal_node:
                error_data = ErrorEventData(
                    code="generation_failed",
                    message="Failed to generate roadmap skeleton.",
                )
                yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"
                return

            # Persist to DB as DRAFT
            milestones_data = [
                {
                    "label": ms.label,
                    "details": ms.details,
                    "order": ms.order,
                    "is_assumed": ms.is_assumed,
                }
                for ms in goal_node.milestones
            ]

            async with self.uow as uow:
                roadmap = await uow.roadmaps.create_skeleton(
                    user_id=user_id,
                    title=request.goal,
                    goal=request.goal,
                    milestones_data=milestones_data,
                    conversation_id=request.conversation_id or None,
                )
                roadmap_id = str(roadmap.id)

            # Re-build goal_node with DB-assigned IDs
            goal_with_db_ids = await self._load_goal_node(roadmap_id)
            if not goal_with_db_ids:
                error_data = ErrorEventData(
                    code="internal_error",
                    message="Failed to load persisted skeleton.",
                )
                yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"
                return

            # Clear actions for skeleton view
            for ms in goal_with_db_ids.milestones:
                ms.actions = []
            goal_with_db_ids.actions = []

            evt = RoadmapSkeletonEvent(
                goal=goal_with_db_ids,
                roadmap_id=roadmap_id,
            )
            yield f"event: roadmap_skeleton\ndata: {evt.model_dump_json()}\n\n"

            logger.info(f"[Skeleton] Completed, roadmap_id={roadmap_id}")

        except Exception as e:
            logger.error(f"[Skeleton] Error: {e}", exc_info=True)
            error_data = ErrorEventData(code="internal_error", message=str(e))
            yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"

    # ------------------------------------------------------------------
    # HIL Step 2: Load from DB → generate actions → persist
    # ------------------------------------------------------------------

    async def stream_actions(
        self,
        roadmap_id: str,
        user_id: str,
        modified_milestones: list[ModifiedMilestone] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Step 2: Generate all actions for a DRAFT roadmap.

        Loads skeleton from DB, generates actions via LLM, persists and activates.
        """
        logger.info(f"[Actions] Starting, roadmap_id={roadmap_id}, modified={modified_milestones is not None}")

        try:
            # If milestones were modified, update DB first
            if modified_milestones:
                await self._apply_milestone_edits(roadmap_id, modified_milestones)

            # Load current state from DB
            goal_node = await self._load_goal_node(roadmap_id)
            if not goal_node:
                error_data = ErrorEventData(
                    code="not_found",
                    message="Roadmap not found. Please regenerate.",
                )
                yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"
                return

            # Load roadmap for context
            async with self.uow as uow:
                roadmap = await uow.roadmaps.get(roadmap_id)
            context = {"goal": roadmap.goal if roadmap else ""}

            # Generate actions via LLM
            final_goal_node = await generate_actions(goal_node, context)

            if not final_goal_node:
                error_data = ErrorEventData(
                    code="generation_failed",
                    message="Failed to generate actions.",
                )
                yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"
                return

            # Persist actions to DB
            await self._persist_actions(roadmap_id, final_goal_node)

            # Yield action events to frontend
            async for sse in self._yield_actions(final_goal_node):
                yield sse

            # Complete
            complete_evt = RoadmapCompleteEvent(roadmap_id=roadmap_id)
            yield f"event: roadmap_complete\ndata: {complete_evt.model_dump_json()}\n\n"

            logger.info(f"[Actions] Completed, roadmap_id={roadmap_id}")

        except Exception as e:
            logger.error(f"[Actions] Error: {e}", exc_info=True)
            error_data = ErrorEventData(code="internal_error", message=str(e))
            yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"

    # ------------------------------------------------------------------
    # Legacy: One-shot generation (no HIL)
    # ------------------------------------------------------------------

    async def stream_roadmap(
        self,
        request: GenerateRoadmapRequest,
        user_id: str | None,
    ) -> AsyncGenerator[str, None]:
        """Legacy: One-shot generation (no HIL). Kept for backward compatibility."""
        if not user_id:
            error_data = ErrorEventData(
                code="auth_required", message="Authentication required"
            )
            yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"
            return

        # Stream skeleton, then immediately stream actions
        roadmap_id = None

        async for event in self.stream_skeleton(request, user_id):
            yield event
            if "roadmap_id" in event:
                import json
                data_start = event.find("data: ") + 6
                data = json.loads(event[data_start:].strip())
                roadmap_id = data.get("roadmap_id")

        if roadmap_id:
            async for event in self.stream_actions(roadmap_id, user_id):
                yield event

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _load_goal_node(self, roadmap_id: str) -> GoalNode | None:
        """Load roadmap from DB and reconstruct as GoalNode tree."""
        async with self.uow as uow:
            roadmap = await uow.roadmaps.get(roadmap_id)
            if not roadmap:
                return None

            # Find goal node
            goal_db = next(
                (n for n in roadmap.nodes if n.type == NodeType.GOAL), None
            )
            if not goal_db:
                return None

            # Build milestone list
            milestones = []
            ms_nodes = sorted(
                [n for n in roadmap.nodes if n.type == NodeType.MILESTONE],
                key=lambda n: n.order,
            )
            for ms_db in ms_nodes:
                # Find actions for this milestone
                action_nodes = sorted(
                    [n for n in roadmap.nodes if n.parent_id == ms_db.id and n.type == NodeType.ACTION],
                    key=lambda n: n.order,
                )
                actions = [
                    {
                        "id": str(a.id),
                        "label": a.label,
                        "type": "action",
                        "details": a.details,
                        "order": a.order,
                        "is_assumed": a.is_assumed,
                    }
                    for a in action_nodes
                ]
                milestones.append(
                    Milestone(
                        id=str(ms_db.id),
                        label=ms_db.label,
                        details=ms_db.details,
                        order=ms_db.order,
                        is_assumed=ms_db.is_assumed,
                        actions=actions,
                    )
                )

            # Direct goal actions
            goal_actions = [
                {
                    "id": str(a.id),
                    "label": a.label,
                    "type": "action",
                    "details": a.details,
                    "order": a.order,
                    "is_assumed": a.is_assumed,
                }
                for a in roadmap.nodes
                if a.parent_id == goal_db.id and a.type == NodeType.ACTION
            ]

            return GoalNode(
                id=str(goal_db.id),
                label=goal_db.label,
                details=goal_db.details,
                milestones=milestones,
                actions=goal_actions,
            )

    async def _apply_milestone_edits(
        self,
        roadmap_id: str,
        modified_milestones: list[ModifiedMilestone],
    ) -> None:
        """Apply user's milestone edits to DB."""
        milestones_data = [
            {
                "label": ms.label,
                "details": ms.details,
                "order": i,
                "is_assumed": False,
            }
            for i, ms in enumerate(modified_milestones)
        ]
        async with self.uow as uow:
            await uow.roadmaps.update_milestones(
                UUID(roadmap_id), milestones_data
            )

    async def _persist_actions(
        self,
        roadmap_id: str,
        goal_node: GoalNode,
    ) -> None:
        """Save generated actions to DB and activate roadmap."""
        milestone_actions: dict[str, list[dict]] = {}

        for ms in goal_node.milestones:
            actions = [
                {
                    "label": a.label if hasattr(a, "label") else a.get("label", ""),
                    "details": a.details if hasattr(a, "details") else a.get("details"),
                    "order": a.order if hasattr(a, "order") else a.get("order", 0),
                    "is_assumed": a.is_assumed if hasattr(a, "is_assumed") else a.get("is_assumed", False),
                }
                for a in (ms.actions if hasattr(ms, "actions") else [])
            ]
            ms_id = ms.id if hasattr(ms, "id") else ms.get("id")
            if actions:
                milestone_actions[ms_id] = actions

        goal_actions = [
            {
                "label": a.label if hasattr(a, "label") else a.get("label", ""),
                "details": a.details if hasattr(a, "details") else a.get("details"),
                "order": a.order if hasattr(a, "order") else a.get("order", 0),
                "is_assumed": a.is_assumed if hasattr(a, "is_assumed") else a.get("is_assumed", False),
            }
            for a in (goal_node.actions if hasattr(goal_node, "actions") else [])
        ]

        async with self.uow as uow:
            await uow.roadmaps.add_actions_to_roadmap(
                UUID(roadmap_id),
                milestone_actions,
                goal_actions or None,
            )

    async def _yield_actions(self, goal_node: GoalNode) -> AsyncGenerator[str, None]:
        """Yield action events for all milestones and direct actions."""
        for ms in goal_node.milestones:
            ms_id = ms.id if hasattr(ms, "id") else ms.get("id")
            actions = ms.actions if hasattr(ms, "actions") else ms.get("actions", [])
            if actions:
                actions_view = [self._to_dict(a) for a in actions]
                evt = RoadmapActionsEvent(milestone_id=ms_id, actions=actions_view)
                yield f"event: roadmap_actions\ndata: {evt.model_dump_json()}\n\n"

        # Direct goal actions
        direct_actions = goal_node.actions if hasattr(goal_node, "actions") else []
        if direct_actions:
            actions_view = [self._to_dict(a) for a in direct_actions]
            evt = RoadmapActionsEvent(milestone_id=None, actions=actions_view)
            yield f"event: roadmap_actions\ndata: {evt.model_dump_json()}\n\n"

    @staticmethod
    def _to_dict(obj) -> dict:
        """Convert object to dict safely."""
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if isinstance(obj, dict):
            return obj
        return dict(obj)

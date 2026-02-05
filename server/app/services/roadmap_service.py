"""
Roadmap Streaming Service (Simplified - No Graph)

Supports 2-step generation flow with HIL:
1. stream_skeleton() - Generates milestone structure for review
2. stream_actions() - Generates actions (original or modified milestones)
"""

import logging
import uuid as uuid_lib
from typing import AsyncGenerator
from uuid import UUID

from app.agents.roadmap.pipeline import generate_actions, generate_skeleton
from app.core.uow import AsyncUnitOfWork
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
        self._skeleton_cache: dict[str, GoalNode] = {}  # thread_id -> skeleton

    def _get_thread_id(self, user_id: str, goal: str) -> str:
        """Generate consistent thread ID for caching."""
        return f"roadmap_{user_id}_{goal[:20].replace(' ', '_')}"

    async def stream_skeleton(
        self,
        request: GenerateRoadmapRequest,
        user_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        Step 1: Generate roadmap skeleton (milestones only).
        
        Returns skeleton for user review. Caches for resumption.
        """
        logger.info(f"[Skeleton] Starting for goal='{request.goal}'")

        context = {
            "goal": request.goal,
            "why": request.why,
            "timeline": request.timeline,
            "obstacles": request.obstacles,
            "resources": request.resources,
        }

        thread_id = self._get_thread_id(user_id, request.goal)

        try:
            # Generate skeleton
            goal_node = await generate_skeleton(context)

            if goal_node:
                # Cache for later resumption
                self._skeleton_cache[thread_id] = goal_node

                goal_dict = self._to_dict(goal_node)
                # Clear actions for skeleton view
                for ms in goal_dict.get("milestones", []):
                    ms["actions"] = []
                goal_dict["actions"] = []

                evt = RoadmapSkeletonEvent(
                    goal=goal_dict,
                    thread_id=thread_id,
                )
                yield f"event: roadmap_skeleton\ndata: {evt.model_dump_json()}\n\n"

            logger.info(f"[Skeleton] Completed, thread_id={thread_id}")

        except Exception as e:
            logger.error(f"[Skeleton] Error: {e}", exc_info=True)
            error_data = ErrorEventData(code="internal_error", message=str(e))
            yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"

    async def stream_actions(
        self,
        thread_id: str,
        user_id: str,
        request: GenerateRoadmapRequest | None = None,
        modified_milestones: list[ModifiedMilestone] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Step 2: Generate all actions.
        
        If modified_milestones provided, uses user's edits.
        Otherwise, uses cached skeleton.
        """
        logger.info(f"[Actions] Starting, thread_id={thread_id}, modified={modified_milestones is not None}")

        context = {
            "goal": request.goal if request else "",
            "why": request.why if request else "",
            "timeline": request.timeline if request else None,
            "obstacles": request.obstacles if request else None,
            "resources": request.resources if request else None,
        }

        try:
            # Get or build goal_node
            if modified_milestones:
                goal_node = self._build_from_modified(modified_milestones, request)
            else:
                goal_node = self._skeleton_cache.get(thread_id)
                if not goal_node:
                    error_data = ErrorEventData(
                        code="not_found",
                        message="Skeleton not found. Please regenerate.",
                    )
                    yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"
                    return

            # Generate actions
            final_goal_node = await generate_actions(goal_node, context)

            if final_goal_node:
                # Yield actions for each milestone
                async for sse in self._yield_actions(final_goal_node):
                    yield sse

                # Persist and complete
                roadmap_id = None
                if user_id and request:
                    roadmap_id = await self._persist_roadmap(
                        request, final_goal_node, user_id
                    )

                if roadmap_id:
                    complete_evt = RoadmapCompleteEvent(roadmap_id=str(roadmap_id))
                    yield f"event: roadmap_complete\ndata: {complete_evt.model_dump_json()}\n\n"

            # Clean up cache
            if thread_id in self._skeleton_cache:
                del self._skeleton_cache[thread_id]

            logger.info("[Actions] Completed")

        except Exception as e:
            logger.error(f"[Actions] Error: {e}", exc_info=True)
            error_data = ErrorEventData(code="internal_error", message=str(e))
            yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"

    def _build_from_modified(
        self,
        modified_milestones: list[ModifiedMilestone],
        request: GenerateRoadmapRequest | None,
    ) -> GoalNode:
        """Build GoalNode from user-modified milestones."""
        goal_id = str(uuid_lib.uuid4())

        milestones = []
        for ms in modified_milestones:
            milestone = Milestone(
                id=ms.id if not ms.is_new else str(uuid_lib.uuid4()),
                label=ms.label,
                details=ms.details,
                type="milestone",
                actions=[],
            )
            milestones.append(milestone)

        return GoalNode(
            id=goal_id,
            label=request.goal if request else "Goal",
            type="goal",
            milestones=milestones,
            actions=[],
        )

    async def stream_roadmap(
        self,
        request: GenerateRoadmapRequest,
        user_id: str | None,
    ) -> AsyncGenerator[str, None]:
        """
        Legacy: One-shot generation (no HIL).
        
        Kept for backward compatibility.
        """
        if not user_id:
            error_data = ErrorEventData(
                code="auth_required", message="Authentication required"
            )
            yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"
            return

        # Stream skeleton then immediately stream actions
        thread_id = None

        async for event in self.stream_skeleton(request, user_id):
            yield event
            if "thread_id" in event:
                import json
                data_start = event.find("data: ") + 6
                data = json.loads(event[data_start:].strip())
                thread_id = data.get("thread_id")

        if thread_id:
            async for event in self.stream_actions(thread_id, user_id, request):
                yield event

    async def _yield_actions(self, goal_node: GoalNode) -> AsyncGenerator[str, None]:
        """Yield action events for all milestones and direct actions."""
        milestones = (
            goal_node.milestones
            if hasattr(goal_node, "milestones")
            else goal_node.get("milestones", [])
        )

        for ms in milestones:
            ms_id = ms.id if hasattr(ms, "id") else ms.get("id")
            actions = ms.actions if hasattr(ms, "actions") else ms.get("actions", [])

            if actions:
                actions_view = [self._to_dict(a) for a in actions]
                evt = RoadmapActionsEvent(milestone_id=ms_id, actions=actions_view)
                yield f"event: roadmap_actions\ndata: {evt.model_dump_json()}\n\n"

        # Direct goal actions
        direct_actions = (
            goal_node.actions
            if hasattr(goal_node, "actions")
            else goal_node.get("actions", [])
        )
        if direct_actions:
            actions_view = [self._to_dict(a) for a in direct_actions]
            evt = RoadmapActionsEvent(milestone_id=None, actions=actions_view)
            yield f"event: roadmap_actions\ndata: {evt.model_dump_json()}\n\n"

    async def _persist_roadmap(
        self,
        request: GenerateRoadmapRequest,
        goal_node: GoalNode,
        user_id: str,
    ) -> UUID | None:
        """Persist roadmap to database."""
        try:
            goal_dict = self._to_dict(goal_node)
            milestones = goal_dict.get("milestones", [])
            goal_actions = goal_dict.get("actions", [])

            logger.info(
                f"Saving roadmap '{request.goal}' with {len(milestones)} milestones"
            )

            async with self.uow as uow:
                existing_roadmap = None
                if request.conversation_id:
                    existing_roadmap = await uow.roadmaps.get_by_conversation_id(
                        request.conversation_id
                    )

                if existing_roadmap:
                    roadmap = await uow.roadmaps.update_with_nodes(
                        roadmap_id=existing_roadmap.id,
                        milestones_data=milestones,
                        goal_actions_data=goal_actions,
                    )
                else:
                    roadmap = await uow.roadmaps.create_with_nodes(
                        user_id=user_id,
                        title=request.goal,
                        goal=request.goal,
                        milestones_data=milestones,
                        goal_actions_data=goal_actions,
                        conversation_id=UUID(request.conversation_id)
                        if request.conversation_id
                        else None,
                    )

                return roadmap.id

        except Exception as e:
            logger.error(f"Failed to persist roadmap: {e}", exc_info=True)
            return None

    @staticmethod
    def _to_dict(obj) -> dict:
        """Convert object to dict safely."""
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if isinstance(obj, dict):
            return obj
        return dict(obj)

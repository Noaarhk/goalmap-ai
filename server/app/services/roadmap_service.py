"""
Roadmap Streaming Service

Handles the business logic for Roadmap Agent streaming:
- Graph execution with LangGraph
- SSE event generation (3-tier: Goal → Milestones → Actions)
- Roadmap persistence
- Langfuse callback integration
"""

import logging
from typing import AsyncGenerator
from uuid import UUID

from app.agents.roadmap.graph import get_graph as get_roadmap_graph

# Removed async_session_factory as it's no longer needed in service
from app.core.graph_manager import GraphManager
from app.core.uow import AsyncUnitOfWork
from app.schemas.api.roadmaps import GenerateRoadmapRequest
from app.schemas.events.base import ErrorEventData
from app.schemas.events.roadmap import (
    RoadmapActionsEvent,
    RoadmapDirectActionsEvent,
    RoadmapSkeletonEvent,
)
from app.services.langfuse import get_langfuse_handler

logger = logging.getLogger(__name__)

# Initialize Roadmap Graph Manager
roadmap_manager = GraphManager(get_roadmap_graph, "roadmap")


class RoadmapStreamService:
    """Service for streaming Roadmap Agent responses."""

    def __init__(self, uow: AsyncUnitOfWork, graph_manager: GraphManager):
        self.uow = uow
        self.graph_manager = graph_manager

    async def stream_roadmap(
        self,
        request: GenerateRoadmapRequest,
        user_id: str | None,
    ) -> AsyncGenerator[str, None]:
        """Execute roadmap graph and yield SSE events."""
        logger.info(f"[Stream] Called for goal='{request.goal}', user_id={user_id}")

        initial_state = {
            "context": {
                "goal": request.goal,
                "why": request.why,
                "timeline": request.timeline,
                "obstacles": request.obstacles,
                "resources": request.resources,
            },
            "goal_node": None,
        }

        try:
            effective_user_id = user_id or "anonymous"
            tags = ["roadmap", "authenticated" if user_id else "anonymous"]

            thread_id = f"roadmap_{effective_user_id}_{request.goal[:10]}"

            langfuse_handler = get_langfuse_handler(
                user_id=effective_user_id, session_id=thread_id, tags=tags
            )
            callbacks = [langfuse_handler] if langfuse_handler else []

            async for event in self.graph_manager.stream_events(
                initial_state,
                thread_id,
                callbacks=callbacks,
            ):
                event_type = event["event"]
                event_name = event.get("name")

                # Handle skeleton generation
                if event_type == "on_chain_end" and event_name == "plan_skeleton":
                    sse_event = await self._handle_skeleton(event)
                    if sse_event:
                        yield sse_event

                # Handle actions generation
                elif event_type == "on_chain_end" and event_name == "generate_actions":
                    async for sse_event in self._handle_actions(event):
                        yield sse_event

                elif (
                    event_type == "on_chain_end"
                    and event_name == "generate_direct_actions"
                ):
                    async for sse_event in self._handle_direct_actions(
                        event, request, user_id
                    ):
                        yield sse_event

            logger.info("[Stream] Generation completed successfully.")

        except Exception as e:
            logger.error(f"[Stream] Critical Error: {e}", exc_info=True)
            error_data = ErrorEventData(code="internal_error", message=str(e))
            yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"

    async def _handle_skeleton(self, event: dict) -> str | None:
        """Handle skeleton output and generate SSE event."""
        output = event["data"].get("output")
        if not output:
            return None

        goal_node = output.get("goal_node")
        if not goal_node:
            return None

        # Convert to dict, clear actions (will be filled later)
        goal_dict = (
            goal_node.model_dump() if hasattr(goal_node, "model_dump") else goal_node
        )
        for ms in goal_dict.get("milestones", []):
            ms["actions"] = []
        goal_dict["actions"] = []

        evt = RoadmapSkeletonEvent(goal=goal_dict)
        return f"event: roadmap_skeleton\ndata: {evt.model_dump_json()}\n\n"

    async def _handle_actions(self, event: dict) -> AsyncGenerator[str, None]:
        """Handle milestone actions and generate SSE events."""
        output = event["data"].get("output")
        if not output:
            return

        goal_node = output.get("goal_node")
        if not goal_node:
            return

        if isinstance(goal_node, dict):
            milestones = goal_node.get("milestones", []) or []
        else:
            milestones = getattr(goal_node, "milestones", []) or []

        for ms in milestones:
            if isinstance(ms, dict):
                actions = ms.get("actions", []) or []
                ms_id = ms.get("id")
            else:
                actions = getattr(ms, "actions", []) or []
                ms_id = ms.id

            if actions:
                actions_view = [
                    a.model_dump() if hasattr(a, "model_dump") else a for a in actions
                ]
                evt = RoadmapActionsEvent(milestone_id=ms_id, actions=actions_view)
                yield f"event: roadmap_actions\ndata: {evt.model_dump_json()}\n\n"

    async def _handle_direct_actions(
        self,
        event: dict,
        request: GenerateRoadmapRequest,
        user_id: str | None,
    ) -> AsyncGenerator[str, None]:
        """Handle direct goal actions, persist roadmap, and generate SSE event."""
        output = event["data"].get("output")
        if not output:
            # If step failed or returned empty output, logging it
            logger.warning("[Stream] generate_direct_actions returned no output")
            return

        goal_node = output.get("goal_node")

        # Persist roadmap (Always persist if we have a valid goal_node at this stage)
        if user_id and goal_node:
            await self._persist_roadmap(request, goal_node, user_id)
        else:
            logger.warning(
                "[Stream] Skipping persistence: No user_id or goal_node missing"
            )

        # Yield direct actions event
        if goal_node:
            direct_actions = getattr(goal_node, "actions", []) or []
            if direct_actions:
                actions_view = [
                    a.model_dump() if hasattr(a, "model_dump") else a
                    for a in direct_actions
                ]
                evt = RoadmapDirectActionsEvent(actions=actions_view)
                yield f"event: roadmap_direct_actions\ndata: {evt.model_dump_json()}\n\n"

    async def _persist_roadmap(
        self,
        request: GenerateRoadmapRequest,
        goal_node: any,
        user_id: str,
    ) -> None:
        """Persist roadmap to database."""
        try:
            logger.info(f"Persisting roadmap for user {user_id}")
            goal_dict = (
                goal_node.model_dump()
                if hasattr(goal_node, "model_dump")
                else goal_node
            )
            logger.info(f"[Service] Goal Dict keys: {goal_dict.keys()}")
            milestones = goal_dict.get("milestones", [])
            goal_actions = goal_dict.get("actions", [])  # Extract direct actions

            logger.info(
                f"Saving roadmap '{request.goal}' with {len(milestones)} milestones and {len(goal_actions)} direct actions"
            )
            if len(milestones) > 0:
                logger.info(f"[Service] First Milestone keys: {milestones[0].keys()}")
            if len(goal_actions) > 0:
                logger.info(f"[Service] First Action keys: {goal_actions[0].keys()}")

            async with self.uow as uow:
                # Check if roadmap exists for this conversation
                existing_roadmap = None
                if request.conversation_id:
                    existing_roadmap = await uow.roadmaps.get_by_conversation_id(
                        request.conversation_id
                    )

                if existing_roadmap:
                    logger.info(f"[Service] Updating roadmap {existing_roadmap.id}")
                    roadmap = await uow.roadmaps.update_with_nodes(
                        roadmap_id=existing_roadmap.id,
                        milestones_data=milestones,
                        goal_actions_data=goal_actions,
                    )
                else:
                    logger.info("[Service] Creating new roadmap")
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

                logger.info(f"Successfully persisted roadmap: {roadmap.id}")
        except Exception as e:
            logger.error(f"Failed to persist roadmap: {e}", exc_info=True)

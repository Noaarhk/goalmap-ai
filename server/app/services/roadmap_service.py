"""
Roadmap Streaming Service

Handles the business logic for Roadmap Agent streaming:
- Graph execution with LangGraph
- SSE event generation
- Roadmap persistence
- Langfuse callback integration
"""

import logging
from typing import AsyncGenerator

from app.agents.roadmap.graph import get_graph as get_roadmap_graph
from app.core.database import async_session_factory
from app.core.graph_manager import GraphManager
from app.repositories.roadmap_repo import RoadmapRepository
from app.schemas.discovery import ErrorEventData
from app.schemas.roadmap import (
    GenerateRoadmapRequest,
    RoadmapMilestonesEvent,
    RoadmapTasksEvent,
)
from app.services.langfuse import get_langfuse_handler

logger = logging.getLogger(__name__)

# Initialize Roadmap Graph Manager
roadmap_manager = GraphManager(get_roadmap_graph, "roadmap")


class RoadmapStreamService:
    """Service for streaming Roadmap Agent responses."""

    @staticmethod
    async def stream_roadmap(
        request: GenerateRoadmapRequest, user_id: str | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute roadmap graph and yield SSE events.

        Args:
            request: Roadmap generation request with goal and context
            user_id: Optional authenticated user ID

        Yields:
            SSE formatted event strings
        """
        initial_state = {
            "goal": request.goal,
            "context": {
                "why": request.why,
                "timeline": request.timeline,
                "obstacles": request.obstacles,
                "resources": request.resources,
            },
            "milestones": [],
        }

        try:
            effective_user_id = user_id or "anonymous"
            tags = ["roadmap", "authenticated" if user_id else "anonymous"]

            # User-specific thread for roadmap persistence
            thread_id = f"roadmap_{effective_user_id}_{request.goal[:10]}"

            # Setup Langfuse Callbacks
            langfuse_handler = get_langfuse_handler(
                user_id=effective_user_id, session_id=thread_id, tags=tags
            )
            callbacks = [langfuse_handler] if langfuse_handler else []

            async for event in roadmap_manager.stream_events(
                initial_state, thread_id, callbacks=callbacks
            ):
                event_type = event["event"]

                # Handle milestones generation
                if event_type == "on_chain_end" and event["name"] == "plan_milestones":
                    sse_event = RoadmapStreamService._handle_milestones(event)
                    if sse_event:
                        yield sse_event

                # Handle tasks generation
                elif event_type == "on_chain_end" and event["name"] == "generate_tasks":
                    async for sse_event in RoadmapStreamService._handle_tasks(
                        event, request, user_id
                    ):
                        yield sse_event

        except Exception as e:
            logger.error(f"Roadmap stream error: {e}")
            error_data = ErrorEventData(code="internal_error", message=str(e))
            yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"

    @staticmethod
    def _handle_milestones(event: dict) -> str | None:
        """Handle milestones output and generate SSE event."""
        output = event["data"].get("output")
        if not output or "milestones" not in output:
            return None

        ms_view = [
            m.model_dump() if hasattr(m, "model_dump") else m
            for m in output["milestones"]
        ]
        for m in ms_view:
            m["tasks"] = []

        evt = RoadmapMilestonesEvent(milestones=ms_view)
        return f"event: roadmap_milestones\ndata: {evt.model_dump_json()}\n\n"

    @staticmethod
    async def _handle_tasks(
        event: dict,
        request: GenerateRoadmapRequest,
        user_id: str | None,
    ) -> AsyncGenerator[str, None]:
        """Handle tasks output, persist roadmap, and generate SSE events."""
        output = event["data"].get("output")
        milestones = output.get("milestones", [])

        # Persist roadmap
        if user_id and milestones:
            await RoadmapStreamService._persist_roadmap(request, milestones, user_id)

        # Yield task events
        for ms in milestones:
            tasks_view = [
                t.model_dump() if hasattr(t, "model_dump") else t for t in ms.tasks
            ]
            if tasks_view:
                evt = RoadmapTasksEvent(milestone_id=ms.id, tasks=tasks_view)
                yield f"event: roadmap_tasks\ndata: {evt.model_dump_json()}\n\n"

    @staticmethod
    async def _persist_roadmap(
        request: GenerateRoadmapRequest,
        milestones: list,
        user_id: str,
    ) -> None:
        """Persist roadmap to database."""
        try:
            async with async_session_factory() as session:
                repo = RoadmapRepository(session)
                roadmap_data = {
                    "user_id": user_id,
                    "title": request.goal,
                    "goal": request.goal,
                    "milestones": [
                        m.model_dump() if hasattr(m, "model_dump") else m
                        for m in milestones
                    ],
                    "conversation_id": None,
                }
                await repo.create(**roadmap_data)
        except Exception as e:
            logger.error(f"Failed to persist roadmap: {e}")

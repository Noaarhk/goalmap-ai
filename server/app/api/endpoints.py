import logging
from typing import AsyncGenerator

from app.agents.discovery.graph import discovery_graph
from app.agents.discovery.state import DiscoveryState
from app.agents.roadmap.graph import roadmap_graph
from app.agents.roadmap.state import RoadmapState
from app.schemas.discovery import (
    BlueprintUpdateEventData,
    ChatRequest,
    ErrorEventData,
    StatusEventData,
    TokenEventData,
)
from app.schemas.roadmap import (
    GenerateRoadmapRequest,
    RoadmapMilestonesEvent,
    RoadmapTasksEvent,
)
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage

router = APIRouter()
logger = logging.getLogger(__name__)

router = APIRouter()
logger = logging.getLogger(__name__)


async def event_generator(request: ChatRequest) -> AsyncGenerator[str, None]:
    """
    Generator that executes the graph and yields SSE events.
    """
    # 1. Prepare Initial State
    messages = []
    for msg in request.history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    # Add current message
    messages.append(HumanMessage(content=request.message))

    initial_state: DiscoveryState = {
        "messages": messages,
        "blueprint": request.current_blueprint or {},
        "user_intent": None,
        "analysis_status": "starting",
    }

    try:
        # 2. Iterate through graph stream events
        async for event in discovery_graph.astream_events(initial_state, version="v1"):
            event_type = event["event"]

            # --- Stream Tokens (Real-time generation) ---
            if event_type == "on_chat_model_stream":
                # We only care about the final response generation for token streaming
                # Filter by node/tag if possible, or just stream all LLM tokens
                # For now, let's assume 'generate_response' is the one we want to stream
                if "generate_response" in event.get("tags", []):
                    content = event["data"]["chunk"].content
                    if content:
                        token_data = TokenEventData(
                            text=content, run_id=event["run_id"]
                        )
                        yield f"event: token\ndata: {token_data.model_dump_json()}\n\n"

            # --- Stream Status Updates (Node Transitions) ---
            elif event_type == "on_chain_start":
                node_name = event["name"]
                # Filter out internal LangGraph names if needed
                if node_name in [
                    "analyze_input",
                    "extract_goal",
                    "extract_tactics",
                    "generate_response",
                ]:
                    status_data = StatusEventData(
                        message=f"Process: {node_name}", node=node_name
                    )
                    yield f"event: status\ndata: {status_data.model_dump_json()}\n\n"

            # --- Stream State Updates (Blueprint) ---
            elif event_type == "on_chain_end":
                # Check if this chain end updated the state with new blueprint info
                output = event["data"].get("output")
                if output and isinstance(output, dict) and "blueprint" in output:
                    # This is a bit of a simplification;
                    # in a real app check diffs or just send full update
                    bp_data = output["blueprint"]
                    # Convert Pydantic model to dict if needed
                    if hasattr(bp_data, "model_dump"):
                        bp_dict = bp_data.model_dump(exclude_none=True)
                    else:
                        bp_dict = bp_data

                    update_data = BlueprintUpdateEventData(**bp_dict)
                    yield f"event: blueprint_update\ndata: {update_data.model_dump_json()}\n\n"

    except Exception as e:
        logger.error(f"Stream error: {e}")
        error_data = ErrorEventData(code="internal_error", message=str(e))
        yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"


@router.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    return StreamingResponse(event_generator(request), media_type="text/event-stream")


# --- Roadmap Generation ---


async def roadmap_event_generator(
    request: GenerateRoadmapRequest,
) -> AsyncGenerator[str, None]:
    """
    Generator for roadmap streaming errors and updates.
    """
    initial_state: RoadmapState = {
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
        async for event in roadmap_graph.astream_events(initial_state, version="v1"):
            event_type = event["event"]

            # 1. Milestones Planned (Skeleton)
            if event_type == "on_chain_end" and event["name"] == "plan_milestones":
                output = event["data"].get("output")
                if output and "milestones" in output:
                    ms_view = [
                        m.model_dump() if hasattr(m, "model_dump") else m
                        for m in output["milestones"]
                    ]
                    # Filter out tasks just in case, only send skeleton first
                    for m in ms_view:
                        m["tasks"] = []

                    evt = RoadmapMilestonesEvent(milestones=ms_view)
                    yield f"event: roadmap_milestones\ndata: {evt.model_dump_json()}\n\n"

            # 2. Tasks Generated (Incremental Update)
            # Since we did a simple sequential generation in nodes.py, this might come as one big update
            # or multiple if we iterated. In our current simplified nodes.py, it returns a full list.
            # Ideally, we should detect when a specific milestone's tasks are updated.
            elif event_type == "on_chain_end" and event["name"] == "generate_tasks":
                output = event["data"].get("output")
                milestones = output.get("milestones", [])
                # In v1 simple implementation, we might just resend the whole thing or individual updates
                # For efficient streaming, let's send each milestone's tasks
                for ms in milestones:
                    tasks_view = [
                        t.model_dump() if hasattr(t, "model_dump") else t
                        for t in ms.tasks
                    ]
                    if tasks_view:
                        evt = RoadmapTasksEvent(milestone_id=ms.id, tasks=tasks_view)
                        yield f"event: roadmap_tasks\ndata: {evt.model_dump_json()}\n\n"

    except Exception as e:
        logger.error(f"Roadmap stream error: {e}")
        error_data = ErrorEventData(code="internal_error", message=str(e))
        yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"


@router.post("/roadmap/stream")
async def stream_roadmap(request: GenerateRoadmapRequest):
    return StreamingResponse(
        roadmap_event_generator(request), media_type="text/event-stream"
    )

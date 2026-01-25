from typing import Any

from app.agents.roadmap.prompts import (
    STRATEGIC_PLANNER_PROMPT,
    TACTICAL_TASK_MANAGER_PROMPT,
)
from app.agents.roadmap.state import RoadmapState
from app.schemas.roadmap import Milestone, Task
from app.services.gemini import get_llm, parse_gemini_output
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

llm = get_llm(model="gemini-3-pro-preview")


async def plan_milestones(state: RoadmapState) -> dict[str, Any]:
    """
    Generates the high-level milestones (skeleton) for the goal.
    """
    goal = state["goal"]
    context = state["context"]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                STRATEGIC_PLANNER_PROMPT,
            ),
            ("human", "Plan the milestones."),
        ]
    )

    chain = prompt | llm | parse_gemini_output | JsonOutputParser()
    try:
        result = await chain.ainvoke({"goal": goal, "context": str(context)})
        milestones_data = result.get("milestones", [])

        # Convert to objects
        milestones = []
        for m in milestones_data:
            milestones.append(Milestone(**m))

        return {"milestones": milestones}
    except Exception as e:
        print(f"Milestone planning error: {e}")
        return {"milestones": []}


async def expand_milestone_tasks(state: RoadmapState) -> dict[str, Any]:
    """
    NOTE: In LangGraph, to run parallel map-reduce style expansion,
    we often handle this orchestration in the graph definition using `Send` API.

    This node function logic is intended to be called for a SINGLE milestone,
    or we can modify it to process all if we don't use the parallel `Send`.

    For simplicity in this v1, let's process them all sequentially here,
    OR (better for streaming) realize that the graph will map this.

    Let's assume this node receives a specific milestone in the state (via Send).
    See graph.py for how we wire this.
    """
    pass  # Implemented in graph logic usually or as a "generate tasks for ALL milestones"


# Alternative: Single node generating tasks for all milestones (easier for v1)
async def generate_tasks_for_all(state: RoadmapState) -> dict[str, Any]:
    milestones = state["milestones"]
    goal = state["goal"]

    # We will just return the same milestones list but populated with tasks.
    # IN REALITY, for true parallel streaming, we want separate nodes.
    # But let's start simple: iterate and generate.

    updated_milestones = []

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                TACTICAL_TASK_MANAGER_PROMPT,
            ),
            ("human", "Generate tasks."),
        ]
    )

    chain = prompt | llm | parse_gemini_output | JsonOutputParser()

    for ms in milestones:
        try:
            result = await chain.ainvoke(
                {
                    "goal": goal,
                    "milestone_label": ms.label,
                    "milestone_details": ms.details,
                }
            )
            tasks_data = result.get("tasks", [])
            tasks = [Task(**t) for t in tasks_data]

            # Create new milestone object with tasks
            new_ms = ms.model_copy()
            new_ms.tasks = tasks
            updated_milestones.append(new_ms)

        except Exception as e:
            print(f"Task gen error for {ms.label}: {e}")
            updated_milestones.append(ms)

    return {"milestones": updated_milestones}  # This replaces the list in state

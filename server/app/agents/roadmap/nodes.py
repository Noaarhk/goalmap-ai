import asyncio
from typing import Any

from app.agents.roadmap.prompts import (
    ACTION_GENERATOR_PROMPT,
    DIRECT_ACTIONS_PROMPT,
    STRATEGIC_PLANNER_PROMPT,
)
from app.agents.roadmap.state import RoadmapState
from app.schemas.llm.roadmap import ActionContent, GoalContent, MilestoneContent
from app.services.gemini import get_llm, parse_gemini_output
from app.utils.roadmap import assign_action_ids, assign_goal_ids
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

llm = get_llm(model="gemini-3-pro-preview")


async def plan_skeleton(state: RoadmapState) -> dict[str, Any]:
    """
    Generates the roadmap skeleton: GoalNode with milestones (empty actions).
    LLM generates content, Backend assigns UUIDs.
    """
    context = state["context"]
    goal_text = context.get("goal", "")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", STRATEGIC_PLANNER_PROMPT),
            ("human", "Create the roadmap skeleton."),
        ]
    )

    chain = prompt | llm | parse_gemini_output | JsonOutputParser()
    try:
        result = await chain.ainvoke({"goal": goal_text, "context": str(context)})

        # Parse LLM output as content (no IDs)
        goal_data = result.get("goal", {})
        milestones_data = goal_data.pop("milestones", [])

        goal_content = GoalContent(
            label=goal_data.get("label", goal_text),
            details=goal_data.get("details"),
            milestones=[MilestoneContent(**ms) for ms in milestones_data],
            actions=[],  # Will be filled later
        )

        # Assign UUIDs
        goal_node = assign_goal_ids(goal_content)

        return {"goal_node": goal_node}
    except Exception as e:
        print(f"Skeleton planning error: {e}")
        return {"goal_node": None}


async def generate_actions(state: RoadmapState) -> dict[str, Any]:
    """
    Generates action items for all milestones.
    LLM generates content, Backend assigns UUIDs.
    """
    goal_node = state["goal_node"]
    if not goal_node:
        return {"goal_node": None}

    context = state["context"]
    goal_text = context.get("goal", "")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ACTION_GENERATOR_PROMPT),
            ("human", "Generate actions."),
        ]
    )

    chain = prompt | llm | parse_gemini_output | JsonOutputParser()

    async def _generate_for_milestone(ms):
        try:
            result = await chain.ainvoke(
                {
                    "goal": goal_text,
                    "milestone_label": ms.label,
                    "milestone_details": ms.details or "",
                }
            )
            actions_data = result.get("actions", [])
            action_contents = [ActionContent(**a) for a in actions_data]
            actions = assign_action_ids(action_contents, ms.id)
            return ms.model_copy(update={"actions": actions})
        except Exception as e:
            print(f"Action gen error for {ms.label}: {e}")
            return ms

    # Run all milestone action generations in parallel
    updated_milestones = await asyncio.gather(
        *[_generate_for_milestone(ms) for ms in goal_node.milestones]
    )

    updated_goal = goal_node.model_copy(update={"milestones": list(updated_milestones)})

    return {"goal_node": updated_goal}


async def generate_direct_actions(state: RoadmapState) -> dict[str, Any]:
    """
    Generates cross-cutting actions directly under the goal.
    LLM generates content, Backend assigns UUIDs.
    """
    goal_node = state["goal_node"]
    if not goal_node:
        return {"goal_node": None}

    context = state["context"]
    goal_text = context.get("goal", "")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", DIRECT_ACTIONS_PROMPT),
            ("human", "Generate direct goal actions."),
        ]
    )

    chain = prompt | llm | parse_gemini_output | JsonOutputParser()

    try:
        result = await chain.ainvoke({"goal": goal_text, "context": str(context)})

        # Parse LLM output as content (no IDs)
        actions_data = result.get("actions", [])
        action_contents = [ActionContent(**a) for a in actions_data]

        # Assign UUIDs
        direct_actions = assign_action_ids(action_contents, goal_node.id)

        # Update goal node with direct actions
        updated_goal = goal_node.model_copy(update={"actions": direct_actions})

        return {"goal_node": updated_goal}
    except Exception as e:
        print(f"Direct actions error: {e}")
        return {"goal_node": goal_node}

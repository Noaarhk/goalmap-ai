"""
Roadmap Generation Pipeline - Simple async functions (no graph needed)

Flow:
1. generate_skeleton() - Generate goal structure with milestones (+ optional direct actions)
2. generate_actions() - Generate actions for all milestones in parallel
"""

import asyncio
import logging
import time
from typing import Any

from app.agents.roadmap.prompts import (
    get_action_generator_prompt,
    get_strategic_planner_prompt,
)
from app.schemas.events.roadmap import GoalNode, Milestone
from app.schemas.llm.roadmap import ActionContent, GoalContent, MilestoneContent
from app.services.gemini import get_llm, parse_gemini_output
from app.utils.roadmap import assign_action_ids, assign_goal_ids
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)

llm = get_llm()  # defaults to gemini-3-flash-preview

__all__ = ["generate_skeleton", "generate_actions", "llm"]


async def generate_skeleton(context: dict[str, Any]) -> GoalNode | None:
    """
    Step 1: Generate roadmap skeleton (Goal + Milestones).

    The LLM may include direct goal-level actions if it deems them necessary
    (e.g. cross-cutting habits like "daily practice" or "track progress").
    """
    goal_text = context.get("goal", "")

    prompt = get_strategic_planner_prompt()
    chain = prompt | llm | parse_gemini_output | JsonOutputParser()

    try:
        logger.info("[Skeleton] Calling LLM...")
        t0 = time.monotonic()
        result = await chain.ainvoke({"goal": goal_text, "context": str(context)})
        logger.info(f"[Skeleton] LLM responded in {time.monotonic() - t0:.1f}s")

        goal_data = result.get("goal", {})
        milestones_data = goal_data.pop("milestones", [])
        actions_data = goal_data.pop("actions", [])

        goal_content = GoalContent(
            label=goal_data.get("label", goal_text),
            details=goal_data.get("details"),
            milestones=[MilestoneContent(**ms) for ms in milestones_data],
            actions=[ActionContent(**a) for a in actions_data],
        )

        return assign_goal_ids(goal_content)

    except Exception as e:
        print(f"Skeleton planning error: {e}")
        return None


async def generate_actions(
    goal_node: GoalNode,
    context: dict[str, Any],
) -> GoalNode | None:
    """
    Step 2: Generate actions for each milestone in parallel.

    Direct goal actions are already set by the skeleton step.
    """
    if not goal_node:
        return None

    goal_text = context.get("goal", "")

    action_prompt = get_action_generator_prompt()
    action_chain = action_prompt | llm | parse_gemini_output | JsonOutputParser()

    async def _generate_for_milestone(ms: Milestone) -> Milestone:
        try:
            logger.info(f"[Actions] Generating for milestone: {ms.label}")
            t0 = time.monotonic()
            result = await action_chain.ainvoke(
                {
                    "goal": goal_text,
                    "milestone_label": ms.label,
                    "milestone_details": ms.details or "",
                }
            )
            logger.info(f"[Actions] '{ms.label}' done in {time.monotonic() - t0:.1f}s")
            actions_data = result.get("actions", [])
            action_contents = [ActionContent(**a) for a in actions_data]
            actions = assign_action_ids(action_contents, ms.id)
            return ms.model_copy(update={"actions": actions})
        except Exception as e:
            logger.error(f"[Actions] Error for '{ms.label}': {e}")
            return ms

    milestones = (
        goal_node.milestones
        if hasattr(goal_node, "milestones")
        else goal_node.get("milestones", [])
    )

    updated_milestones = await asyncio.gather(
        *[_generate_for_milestone(ms) for ms in milestones]
    )

    return goal_node.model_copy(update={"milestones": list(updated_milestones)})

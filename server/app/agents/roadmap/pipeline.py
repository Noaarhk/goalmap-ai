"""
Roadmap Generation Pipeline - Simple async functions (no graph needed)

Flow:
1. generate_skeleton() - Generate goal structure with milestones
2. generate_actions() - Generate actions for all milestones + direct goal actions
"""

import asyncio
from typing import Any

from app.agents.roadmap.prompts import (
    ACTION_GENERATOR_PROMPT,
    DIRECT_ACTIONS_PROMPT,
    STRATEGIC_PLANNER_PROMPT,
)
from app.schemas.events.roadmap import GoalNode, Milestone
from app.schemas.llm.roadmap import ActionContent, GoalContent, MilestoneContent
from app.services.gemini import get_llm, parse_gemini_output
from app.utils.roadmap import assign_action_ids, assign_goal_ids
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

llm = get_llm(model="gemini-3-pro-preview")

__all__ = ["generate_skeleton", "generate_actions", "llm"]


async def generate_skeleton(context: dict[str, Any]) -> GoalNode | None:
    """
    Step 1: Generate roadmap skeleton (Goal + Milestones, no actions).
    
    Args:
        context: Dict with goal, why, timeline, obstacles, resources
        
    Returns:
        GoalNode with milestones (actions empty) or None on failure
    """
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

        goal_data = result.get("goal", {})
        milestones_data = goal_data.pop("milestones", [])

        goal_content = GoalContent(
            label=goal_data.get("label", goal_text),
            details=goal_data.get("details"),
            milestones=[MilestoneContent(**ms) for ms in milestones_data],
            actions=[],
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
    Step 2: Generate all actions (milestone actions + direct goal actions).
    
    Args:
        goal_node: GoalNode with milestones (from skeleton or modified by user)
        context: Dict with goal, why, timeline, obstacles, resources
        
    Returns:
        GoalNode with all actions filled in, or None on failure
    """
    if not goal_node:
        return None

    goal_text = context.get("goal", "")

    # --- Generate milestone actions in parallel ---
    action_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ACTION_GENERATOR_PROMPT),
            ("human", "Generate actions."),
        ]
    )
    action_chain = action_prompt | llm | parse_gemini_output | JsonOutputParser()

    async def _generate_for_milestone(ms: Milestone) -> Milestone:
        try:
            result = await action_chain.ainvoke(
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

    # Get milestones (handle both object and dict)
    milestones = (
        goal_node.milestones
        if hasattr(goal_node, "milestones")
        else goal_node.get("milestones", [])
    )

    updated_milestones = await asyncio.gather(
        *[_generate_for_milestone(ms) for ms in milestones]
    )

    # --- Generate direct goal actions ---
    direct_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", DIRECT_ACTIONS_PROMPT),
            ("human", "Generate direct goal actions."),
        ]
    )
    direct_chain = direct_prompt | llm | parse_gemini_output | JsonOutputParser()

    try:
        result = await direct_chain.ainvoke(
            {"goal": goal_text, "context": str(context)}
        )
        actions_data = result.get("actions", [])
        action_contents = [ActionContent(**a) for a in actions_data]
        
        goal_id = goal_node.id if hasattr(goal_node, "id") else goal_node.get("id")
        direct_actions = assign_action_ids(action_contents, goal_id)
    except Exception as e:
        print(f"Direct actions error: {e}")
        direct_actions = []

    # --- Combine everything ---
    return goal_node.model_copy(
        update={
            "milestones": list(updated_milestones),
            "actions": direct_actions,
        }
    )

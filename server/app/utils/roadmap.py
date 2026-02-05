from uuid import uuid4

from app.schemas.events.roadmap import ActionNode, GoalNode, Milestone
from app.schemas.llm.roadmap import ActionContent, GoalContent, MilestoneContent


def assign_action_ids(actions: list[ActionContent], prefix: str) -> list[ActionNode]:
    """Assign UUIDs to action contents."""
    return [
        ActionNode(
            id=f"{prefix}-{str(uuid4())[:8]}",
            label=a.label,
            details=a.details,
            is_assumed=a.is_assumed,
            order=i,
        )
        for i, a in enumerate(actions)
    ]


def assign_milestone_ids(milestones: list[MilestoneContent]) -> list[Milestone]:
    """Assign UUIDs to milestone contents and their actions."""
    result = []
    for i, ms in enumerate(milestones):
        ms_id = f"ms-{str(uuid4())[:8]}"
        result.append(
            Milestone(
                id=ms_id,
                label=ms.label,
                details=ms.details,
                is_assumed=ms.is_assumed,
                order=i,
                actions=assign_action_ids(ms.actions, ms_id),
            )
        )
    return result


def assign_goal_ids(goal: GoalContent) -> GoalNode:
    """Assign UUIDs to goal content and all children."""
    goal_id = f"goal-{str(uuid4())[:8]}"
    return GoalNode(
        id=goal_id,
        label=goal.label,
        details=goal.details,
        milestones=assign_milestone_ids(goal.milestones),
        actions=assign_action_ids(goal.actions, goal_id),
    )

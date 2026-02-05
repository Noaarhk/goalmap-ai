from app.models.node import Node, NodeStatus, NodeType
from app.models.roadmap import Roadmap
from app.repositories.base import BaseRepository
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class RoadmapRepository(BaseRepository[Roadmap]):
    def __init__(self, db):
        super().__init__(Roadmap, db)

    async def create_with_nodes(
        self,
        user_id: str,
        title: str,
        goal: str,
        milestones_data: list[dict],
        goal_actions_data: list[dict] = None,
        conversation_id: str | None = None,
    ) -> Roadmap:
        """
        Create a roadmap with hierarchical nodes (milestones -> actions) and direct goal actions.
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.info(f"[Repo] Creating roadmap for user={user_id}, title={title}")

        # 1. Create Roadmap
        roadmap = Roadmap(
            user_id=user_id,
            title=title,
            goal=goal,
            conversation_id=conversation_id,
        )
        self.db.add(roadmap)
        await self.db.flush()  # Generate ID
        logger.info(f"[Repo] Roadmap created with ID: {roadmap.id}")

        # 2. Create Goal Node (Implicit top-level logic, but we treat goal as metadata.
        # Actually Roadmap IS the goal container. The nodes linked to roadmap_id are children.
        # But we need "Direct Actions" which are linked to the Roadmap (acting as Goal) directly?)
        # Our model: Nodes have parent_id.
        # Milestones: parent_id = None (or Roadmap ID conceptually)
        # Goal Actions: parent_id = None? Or linked to a Goal Node?
        # The schema has a 'GoalNode' type.
        # Currently we only created Milestone Nodes (Level 1).

        # If we follow the schema: GoalNode is the root.
        # But in DB, we Flat store Nodes.
        # We need a Root Node of type 'goal'?
        # Let's check visualization. Visualization expects a 'goal' node.

        # Checking current repo... NO goal node created??
        # The frontend renders 'goal' node from roadmap metadata usually?
        # Wait, visualization.tsx expects a NODE with type='goal'.
        # Previous logic:
        # User: "create_with_nodes"
        # It creates Roadmap.
        # It creates Milestone Nodes.
        # Where is the GOAL NODE?
        # Frontend: const goalNode = data.nodes.find((n: any) => n.type === "goal");

        # IF WE DON'T CREATE A GOAL NODE IN DB, FRONTEND WON'T FIND IT.
        # And Direct Actions need a parent.

        # FIX: Create a GOAL Node first.

        goal_node = Node(
            roadmap_id=roadmap.id,
            type=NodeType.GOAL,
            label=goal,
            details=title,  # or description if available
            status=NodeStatus.PENDING,
        )
        self.db.add(goal_node)
        await self.db.flush()  # Need ID
        logger.info(f"[Repo] Goal Node created: {goal_node.id}")

        # 3. Create Nodes

        # Direct Goal Actions
        if goal_actions_data:
            logger.info(f"[Repo] Processing {len(goal_actions_data)} direct actions")
            for i, a_data in enumerate(goal_actions_data):
                action_node = Node(
                    roadmap_id=roadmap.id,
                    parent_id=goal_node.id,  # Linked to Goal Node
                    type=NodeType.ACTION,
                    label=a_data.get("label"),
                    details=a_data.get("details"),
                    order=a_data.get("order", 0),
                    is_assumed=a_data.get("is_assumed", False),
                    status=NodeStatus(a_data.get("status", "pending")),
                )
                self.db.add(action_node)
                if i == 0 or i == len(goal_actions_data) - 1:
                    logger.info(f"[Repo] Direct Action added: {a_data.get('label')}")

        # Create all milestone nodes in bulk, then flush once to get IDs
        logger.info(f"[Repo] Processing {len(milestones_data)} milestones")
        milestone_nodes = []
        for m_data in milestones_data:
            milestone_node = Node(
                roadmap_id=roadmap.id,
                parent_id=goal_node.id,
                type=NodeType.MILESTONE,
                label=m_data.get("label"),
                details=m_data.get("details"),
                order=m_data.get("order", 0),
                is_assumed=m_data.get("is_assumed", False),
                status=NodeStatus.PENDING,
            )
            self.db.add(milestone_node)
            milestone_nodes.append((milestone_node, m_data))

        await self.db.flush()  # Single flush for all milestones

        # Create all action nodes using the now-available milestone IDs
        for milestone_node, m_data in milestone_nodes:
            for a_data in m_data.get("actions", []):
                action_node = Node(
                    roadmap_id=roadmap.id,
                    parent_id=milestone_node.id,
                    type=NodeType.ACTION,
                    label=a_data.get("label"),
                    details=a_data.get("details"),
                    order=a_data.get("order", 0),
                    is_assumed=a_data.get("is_assumed", False),
                    status=NodeStatus(a_data.get("status", "pending")),
                )
                self.db.add(action_node)

        await self.db.commit()
        await self.db.refresh(roadmap)
        logger.info("[Repo] Commit successful")
        return roadmap

    async def get_by_user_id(self, user_id: str) -> list[Roadmap]:
        query = (
            select(Roadmap)
            .where(Roadmap.user_id == user_id)
            .options(selectinload(Roadmap.nodes))
            .order_by(Roadmap.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_with_nodes(
        self,
        roadmap_id: str,
        milestones_data: list[dict],
        goal_actions_data: list[dict] = None,
    ) -> Roadmap:
        """
        Update roadmap nodes by replacing them (Delete All + Create New).
        """
        roadmap = await self.get(roadmap_id)
        if not roadmap:
            return None

        # 1. Delete existing nodes
        query = select(Node).where(Node.roadmap_id == roadmap_id)
        result = await self.db.execute(query)
        existing_nodes = result.scalars().all()
        for n in existing_nodes:
            await self.db.delete(n)

        await self.db.flush()

        # Re-create Goal Node?
        # Yes, we wiped everything.
        goal_node = Node(
            roadmap_id=roadmap.id,
            type=NodeType.GOAL,
            label=roadmap.goal,
            details=roadmap.title,
            status=NodeStatus.PENDING,
        )
        self.db.add(goal_node)
        await self.db.flush()

        # 2. Create new nodes

        # Direct Goal Actions
        if goal_actions_data:
            for a_data in goal_actions_data:
                action_node = Node(
                    roadmap_id=roadmap_id,
                    parent_id=goal_node.id,
                    type=NodeType.ACTION,
                    label=a_data.get("label"),
                    details=a_data.get("details"),
                    order=a_data.get("order", 0),
                    is_assumed=a_data.get("is_assumed", False),
                    status=NodeStatus(a_data.get("status", "pending")),
                )
                self.db.add(action_node)

        milestone_nodes = []
        for m_data in milestones_data:
            milestone_node = Node(
                roadmap_id=roadmap_id,
                parent_id=goal_node.id,
                type=NodeType.MILESTONE,
                label=m_data.get("label"),
                details=m_data.get("details"),
                order=m_data.get("order", 0),
                is_assumed=m_data.get("is_assumed", False),
                status=NodeStatus(m_data.get("status", "pending")),
            )
            self.db.add(milestone_node)
            milestone_nodes.append((milestone_node, m_data))

        await self.db.flush()  # Single flush for all milestones

        for milestone_node, m_data in milestone_nodes:
            for a_data in m_data.get("actions", []):
                action_node = Node(
                    roadmap_id=roadmap_id,
                    parent_id=milestone_node.id,
                    type=NodeType.ACTION,
                    label=a_data.get("label"),
                    details=a_data.get("details"),
                    order=a_data.get("order", 0),
                    is_assumed=a_data.get("is_assumed", False),
                    status=NodeStatus(a_data.get("status", "pending")),
                )
                self.db.add(action_node)

        await self.db.commit()
        await self.db.refresh(roadmap)
        return roadmap

    async def get(self, id: str) -> Roadmap | None:
        query = (
            select(Roadmap).where(Roadmap.id == id).options(selectinload(Roadmap.nodes))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_conversation_id(self, conversation_id: str) -> Roadmap | None:
        query = (
            select(Roadmap)
            .where(Roadmap.conversation_id == conversation_id)
            .options(selectinload(Roadmap.nodes))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

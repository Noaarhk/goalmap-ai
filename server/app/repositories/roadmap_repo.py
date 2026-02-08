import logging
from uuid import UUID

from app.models.node import Node, NodeStatus, NodeType
from app.models.roadmap import Roadmap, RoadmapStatus
from app.repositories.base import BaseRepository
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class RoadmapRepository(BaseRepository[Roadmap]):
    def __init__(self, db):
        super().__init__(Roadmap, db)

    # ------------------------------------------------------------------
    # HIL Step 1: Create skeleton (Roadmap + Goal + Milestones, no actions)
    # ------------------------------------------------------------------

    async def create_skeleton(
        self,
        user_id: str,
        title: str,
        goal: str,
        milestones_data: list[dict],
        conversation_id: str | None = None,
    ) -> Roadmap:
        """Create a DRAFT roadmap with goal node and milestone nodes (no actions yet)."""
        logger.info(f"[Repo] Creating skeleton for user={user_id}, goal='{title}'")

        # Check if a roadmap already exists for this conversation
        existing = None
        if conversation_id:
            existing = await self.get_by_conversation_id(conversation_id)

        if existing:
            # Replace nodes on existing roadmap instead of creating a new one
            logger.info(
                f"[Repo] Existing roadmap found ({existing.id}), replacing skeleton"
            )
            return await self._replace_skeleton(existing, milestones_data)

        # 1. Create Roadmap (DRAFT)
        roadmap = Roadmap(
            user_id=user_id,
            title=title,
            goal=goal,
            status=RoadmapStatus.DRAFT,
            conversation_id=conversation_id,
        )
        self.db.add(roadmap)
        await self.db.flush()

        # 2. Goal Node
        goal_node = Node(
            roadmap_id=roadmap.id,
            type=NodeType.GOAL,
            label=goal,
            details=title,
            status=NodeStatus.PENDING,
        )
        self.db.add(goal_node)
        await self.db.flush()

        # 3. Milestone Nodes
        for i, m in enumerate(milestones_data):
            ms_node = Node(
                roadmap_id=roadmap.id,
                parent_id=goal_node.id,
                type=NodeType.MILESTONE,
                label=m.get("label", ""),
                details=m.get("details"),
                order=m.get("order", i),
                is_assumed=m.get("is_assumed", False),
                start_date=m.get("start_date"),
                end_date=m.get("end_date"),
                completion_criteria=m.get("completion_criteria"),
                status=NodeStatus.PENDING,
            )
            self.db.add(ms_node)

        await self.db.flush()
        logger.info(
            f"[Repo] Skeleton created: roadmap_id={roadmap.id}, milestones={len(milestones_data)}"
        )
        return roadmap

    async def _replace_skeleton(
        self,
        roadmap: Roadmap,
        milestones_data: list[dict],
    ) -> Roadmap:
        """Replace all nodes on an existing roadmap with a new skeleton."""
        # Delete existing nodes
        query = select(Node).where(Node.roadmap_id == roadmap.id)
        result = await self.db.execute(query)
        for n in result.scalars().all():
            await self.db.delete(n)
        await self.db.flush()

        # Re-create goal + milestones
        goal_node = Node(
            roadmap_id=roadmap.id,
            type=NodeType.GOAL,
            label=roadmap.goal,
            details=roadmap.title,
            status=NodeStatus.PENDING,
        )
        self.db.add(goal_node)
        await self.db.flush()

        for i, m in enumerate(milestones_data):
            ms_node = Node(
                roadmap_id=roadmap.id,
                parent_id=goal_node.id,
                type=NodeType.MILESTONE,
                label=m.get("label", ""),
                details=m.get("details"),
                order=m.get("order", i),
                is_assumed=m.get("is_assumed", False),
                start_date=m.get("start_date"),
                end_date=m.get("end_date"),
                completion_criteria=m.get("completion_criteria"),
                status=NodeStatus.PENDING,
            )
            self.db.add(ms_node)

        await self.db.flush()
        roadmap.status = RoadmapStatus.DRAFT
        return roadmap

    # ------------------------------------------------------------------
    # HIL Step 2: Add actions to existing milestone nodes
    # ------------------------------------------------------------------

    async def add_actions_to_roadmap(
        self,
        roadmap_id: UUID,
        milestone_actions: dict[str, list[dict]],
        goal_actions: list[dict] | None = None,
    ) -> Roadmap:
        """
        Add action nodes under each milestone.

        Args:
            roadmap_id: The roadmap UUID
            milestone_actions: {milestone_node_id: [action_dicts]}
            goal_actions: Optional direct goal-level actions
        """
        roadmap = await self.get(roadmap_id)
        if not roadmap:
            return None

        # Find goal node for direct actions
        goal_node = next((n for n in roadmap.nodes if n.type == NodeType.GOAL), None)

        # Add milestone actions
        for ms_id_str, actions in milestone_actions.items():
            ms_id = UUID(ms_id_str) if isinstance(ms_id_str, str) else ms_id_str
            for i, a in enumerate(actions):
                action_node = Node(
                    roadmap_id=roadmap_id,
                    parent_id=ms_id,
                    type=NodeType.ACTION,
                    label=a.get("label", ""),
                    details=a.get("details"),
                    order=a.get("order", i),
                    is_assumed=a.get("is_assumed", False),
                    status=NodeStatus.PENDING,
                )
                self.db.add(action_node)

        # Add direct goal actions
        if goal_actions and goal_node:
            for i, a in enumerate(goal_actions):
                action_node = Node(
                    roadmap_id=roadmap_id,
                    parent_id=goal_node.id,
                    type=NodeType.ACTION,
                    label=a.get("label", ""),
                    details=a.get("details"),
                    order=a.get("order", i),
                    is_assumed=a.get("is_assumed", False),
                    status=NodeStatus.PENDING,
                )
                self.db.add(action_node)

        await self.db.flush()

        # Activate roadmap
        roadmap.status = RoadmapStatus.ACTIVE
        await self.db.flush()

        logger.info(f"[Repo] Actions added to roadmap {roadmap_id}, status=ACTIVE")
        return roadmap

    # ------------------------------------------------------------------
    # HIL: Update milestones (user edits before approval)
    # ------------------------------------------------------------------

    async def update_milestones(
        self,
        roadmap_id: UUID,
        milestones_data: list[dict],
    ) -> Roadmap:
        """
        Replace milestone nodes on a DRAFT roadmap (user modified during review).
        Keeps the goal node, replaces milestones.
        """
        roadmap = await self.get(roadmap_id)
        if not roadmap:
            return None

        # Find and keep goal node, delete milestones (and their actions)
        goal_node = next((n for n in roadmap.nodes if n.type == NodeType.GOAL), None)
        if not goal_node:
            raise ValueError(f"Roadmap {roadmap_id} has no goal node")

        # Delete milestone nodes (cascades to their action children)
        query = select(Node).where(
            Node.roadmap_id == roadmap_id,
            Node.type == NodeType.MILESTONE,
        )
        result = await self.db.execute(query)
        for n in result.scalars().all():
            await self.db.delete(n)
        await self.db.flush()

        # Re-create milestones
        for i, m in enumerate(milestones_data):
            ms_node = Node(
                roadmap_id=roadmap_id,
                parent_id=goal_node.id,
                type=NodeType.MILESTONE,
                label=m.get("label", ""),
                details=m.get("details"),
                order=m.get("order", i),
                is_assumed=m.get("is_assumed", False),
                start_date=m.get("start_date"),
                end_date=m.get("end_date"),
                completion_criteria=m.get("completion_criteria"),
                status=NodeStatus.PENDING,
            )
            self.db.add(ms_node)

        await self.db.flush()
        logger.info(f"[Repo] Milestones updated for roadmap {roadmap_id}")
        return roadmap

    # ------------------------------------------------------------------
    # Full create (legacy one-shot)
    # ------------------------------------------------------------------

    async def create_with_nodes(
        self,
        user_id: str,
        title: str,
        goal: str,
        milestones_data: list[dict],
        goal_actions_data: list[dict] = None,
        conversation_id: str | None = None,
    ) -> Roadmap:
        """Create a roadmap with full node hierarchy (milestones + actions)."""
        logger.info(f"[Repo] Creating full roadmap for user={user_id}, title={title}")

        roadmap = Roadmap(
            user_id=user_id,
            title=title,
            goal=goal,
            status=RoadmapStatus.ACTIVE,
            conversation_id=conversation_id,
        )
        self.db.add(roadmap)
        await self.db.flush()

        goal_node = Node(
            roadmap_id=roadmap.id,
            type=NodeType.GOAL,
            label=goal,
            details=title,
            status=NodeStatus.PENDING,
        )
        self.db.add(goal_node)
        await self.db.flush()

        # Direct Goal Actions
        if goal_actions_data:
            for i, a_data in enumerate(goal_actions_data):
                action_node = Node(
                    roadmap_id=roadmap.id,
                    parent_id=goal_node.id,
                    type=NodeType.ACTION,
                    label=a_data.get("label"),
                    details=a_data.get("details"),
                    order=a_data.get("order", 0),
                    is_assumed=a_data.get("is_assumed", False),
                    status=NodeStatus(a_data.get("status", "pending")),
                )
                self.db.add(action_node)

        # Milestones + Actions
        milestone_nodes = []
        for m_data in milestones_data:
            ms_node = Node(
                roadmap_id=roadmap.id,
                parent_id=goal_node.id,
                type=NodeType.MILESTONE,
                label=m_data.get("label"),
                details=m_data.get("details"),
                order=m_data.get("order", 0),
                is_assumed=m_data.get("is_assumed", False),
                status=NodeStatus.PENDING,
            )
            self.db.add(ms_node)
            milestone_nodes.append((ms_node, m_data))

        await self.db.flush()

        for ms_node, m_data in milestone_nodes:
            for a_data in m_data.get("actions", []):
                action_node = Node(
                    roadmap_id=roadmap.id,
                    parent_id=ms_node.id,
                    type=NodeType.ACTION,
                    label=a_data.get("label"),
                    details=a_data.get("details"),
                    order=a_data.get("order", 0),
                    is_assumed=a_data.get("is_assumed", False),
                    status=NodeStatus(a_data.get("status", "pending")),
                )
                self.db.add(action_node)

        await self.db.flush()
        return roadmap

    # ------------------------------------------------------------------
    # Update (replace all nodes)
    # ------------------------------------------------------------------

    async def update_with_nodes(
        self,
        roadmap_id: str,
        milestones_data: list[dict],
        goal_actions_data: list[dict] = None,
    ) -> Roadmap:
        """Update roadmap nodes by replacing them."""
        roadmap = await self.get(roadmap_id)
        if not roadmap:
            return None

        # Delete existing nodes
        query = select(Node).where(Node.roadmap_id == roadmap_id)
        result = await self.db.execute(query)
        for n in result.scalars().all():
            await self.db.delete(n)
        await self.db.flush()

        # Re-create
        goal_node = Node(
            roadmap_id=roadmap.id,
            type=NodeType.GOAL,
            label=roadmap.goal,
            details=roadmap.title,
            status=NodeStatus.PENDING,
        )
        self.db.add(goal_node)
        await self.db.flush()

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
            ms_node = Node(
                roadmap_id=roadmap_id,
                parent_id=goal_node.id,
                type=NodeType.MILESTONE,
                label=m_data.get("label"),
                details=m_data.get("details"),
                order=m_data.get("order", 0),
                is_assumed=m_data.get("is_assumed", False),
                status=NodeStatus(m_data.get("status", "pending")),
            )
            self.db.add(ms_node)
            milestone_nodes.append((ms_node, m_data))

        await self.db.flush()

        for ms_node, m_data in milestone_nodes:
            for a_data in m_data.get("actions", []):
                action_node = Node(
                    roadmap_id=roadmap_id,
                    parent_id=ms_node.id,
                    type=NodeType.ACTION,
                    label=a_data.get("label"),
                    details=a_data.get("details"),
                    order=a_data.get("order", 0),
                    is_assumed=a_data.get("is_assumed", False),
                    status=NodeStatus(a_data.get("status", "pending")),
                )
                self.db.add(action_node)

        await self.db.flush()
        return roadmap

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get(self, id: str) -> Roadmap | None:
        query = (
            select(Roadmap).where(Roadmap.id == id).options(selectinload(Roadmap.nodes))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> list[Roadmap]:
        query = (
            select(Roadmap)
            .where(Roadmap.user_id == user_id)
            .options(selectinload(Roadmap.nodes))
            .order_by(Roadmap.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_conversation_id(self, conversation_id: str) -> Roadmap | None:
        query = (
            select(Roadmap)
            .where(Roadmap.conversation_id == conversation_id)
            .options(selectinload(Roadmap.nodes))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

import logging
from typing import Any, AsyncGenerator

from app.core.database import get_postgres_saver
from langgraph.graph.state import CompiledStateGraph

logger = logging.getLogger(__name__)


class GraphManager:
    """
    Manages the lifecycle and execution of LangGraph agents.
    Handles:
    - Graph compilation
    - Checkpointer injection (Postgres)
    - Callback configuration (Langfuse)
    - Streaming execution
    """

    def __init__(self, graph_factory, graph_name: str):
        self.graph_factory = graph_factory  # Function that returns compiled graph
        self.graph_name = graph_name

    async def stream_events(
        self,
        initial_state: dict[str, Any],
        thread_id: str | None = None,
        callbacks: list | None = None,
        version: str = "v1",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Executes the graph and yields events.
        Manages checkpointer context.
        """
        # Default thread_id if not provided (stateless/transient run)
        if not thread_id:
            thread_id = "default_thread"

        config = {"configurable": {"thread_id": thread_id}}
        if callbacks:
            config["callbacks"] = callbacks

        # Context Manage Checkpointer
        try:
            async with get_postgres_saver() as checkpointer:
                # Compile graph with checkpointer at runtime
                graph: CompiledStateGraph = self.graph_factory(checkpointer)

                async for event in graph.astream_events(
                    initial_state, config=config, version=version
                ):
                    yield event

        except Exception as e:
            logger.error(f"Error executing graph {self.graph_name}: {e}")
            raise e

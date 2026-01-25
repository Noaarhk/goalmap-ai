"""
Optimized Discovery Graph v3 - Pipeline Architecture
Flow: START -> analyze_turn (Extraction) -> generate_chat (Response) -> END
"""

from app.agents.discovery.nodes import analyze_turn, generate_chat
from app.agents.discovery.state import DiscoveryState
from langgraph.graph import END, START, StateGraph

# Build Graph
graph_builder = StateGraph(DiscoveryState)

# Add Nodes
graph_builder.add_node("analyze_turn", analyze_turn)
graph_builder.add_node("generate_chat", generate_chat)

# Add Edges: Sequential Flow
graph_builder.add_edge(START, "analyze_turn")
graph_builder.add_edge("analyze_turn", "generate_chat")
graph_builder.add_edge("generate_chat", END)


def get_graph(checkpointer=None):
    """Returns the discovery pipeline graph."""
    return graph_builder.compile(checkpointer=checkpointer)


discovery_graph = get_graph()

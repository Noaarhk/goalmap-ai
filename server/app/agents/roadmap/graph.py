from app.agents.roadmap.nodes import (
    generate_actions,
    generate_direct_actions,
    plan_skeleton,
)
from app.agents.roadmap.state import RoadmapState
from langgraph.graph import END, START, StateGraph

# Build Graph for 3-tier Roadmap Generation
graph_builder = StateGraph(RoadmapState)

# Nodes
graph_builder.add_node("plan_skeleton", plan_skeleton)
graph_builder.add_node("generate_actions", generate_actions)
graph_builder.add_node("generate_direct_actions", generate_direct_actions)

# Linear flow: Skeleton → Milestone Actions → Direct Goal Actions
graph_builder.add_edge(START, "plan_skeleton")
graph_builder.add_edge("plan_skeleton", "generate_actions")
graph_builder.add_edge("generate_actions", "generate_direct_actions")
graph_builder.add_edge("generate_direct_actions", END)


# Compile
def get_graph(checkpointer=None):
    return graph_builder.compile(checkpointer=checkpointer)


roadmap_graph = get_graph()

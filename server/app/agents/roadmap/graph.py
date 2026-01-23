from app.agents.roadmap.nodes import generate_tasks_for_all, plan_milestones
from app.agents.roadmap.state import RoadmapState
from langgraph.graph import END, START, StateGraph

# Build Graph
graph_builder = StateGraph(RoadmapState)

graph_builder.add_node("plan_milestones", plan_milestones)
graph_builder.add_node("generate_tasks", generate_tasks_for_all)

# Simple Linear Edge for v1
graph_builder.add_edge(START, "plan_milestones")
graph_builder.add_edge("plan_milestones", "generate_tasks")
graph_builder.add_edge("generate_tasks", END)

# Compile
roadmap_graph = graph_builder.compile()

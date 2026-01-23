from app.agents.discovery.nodes import (
    analyze_input,
    extract_goal,
    extract_tactics,
    generate_response,
)
from app.agents.discovery.state import DiscoveryState
from langgraph.graph import END, START, StateGraph


def route_based_on_intent(state: DiscoveryState):
    """
    Dynamic routing logic.
    """
    intent = state.get("user_intent")

    if intent == "greeting":
        return "generate_response"
    elif intent == "providing_info":
        return "extract_goal"  # Default to checking goal first
    else:
        return "generate_response"


def route_after_goal(state: DiscoveryState):
    """
    After extracting goal, check if we need tactics or just response.
    """
    blueprint = state["blueprint"]
    if blueprint.fieldScores.goal > 50 and blueprint.fieldScores.why > 50:
        return "extract_tactics"
    return "generate_response"


# Build Graph
graph_builder = StateGraph(DiscoveryState)

graph_builder.add_node("analyze_input", analyze_input)
graph_builder.add_node("extract_goal", extract_goal)
graph_builder.add_node("extract_tactics", extract_tactics)
graph_builder.add_node("generate_response", generate_response)

# Edges
graph_builder.add_edge(START, "analyze_input")

graph_builder.add_conditional_edges(
    "analyze_input",
    route_based_on_intent,
    {"generate_response": "generate_response", "extract_goal": "extract_goal"},
)

graph_builder.add_conditional_edges(
    "extract_goal",
    route_after_goal,
    {"extract_tactics": "extract_tactics", "generate_response": "generate_response"},
)

graph_builder.add_edge("extract_tactics", "generate_response")
graph_builder.add_edge("generate_response", END)

# Compile
discovery_graph = graph_builder.compile()

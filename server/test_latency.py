#!/usr/bin/env python3
"""
Performance + Quality test for Discovery Chat v2.
"""

import asyncio
import sys
import time

from dotenv import load_dotenv

load_dotenv("/Users/noah/goalmap-ai/.env.local")

sys.path.insert(0, "/Users/noah/goalmap-ai/server")

from app.agents.discovery.graph import get_graph
from app.schemas.discovery import BlueprintData, FieldScores
from langchain_core.messages import AIMessage, HumanMessage


async def test_v2_quality():
    """Test v2 graph and show full response for quality check."""

    graph = get_graph()

    # Test input
    state = {
        "messages": [
            AIMessage(content="Greetings, Traveler. I am the Oracle."),
            HumanMessage(
                content="나는 2달내로 백엔드 엔지니어로 이직하고 싶어 현재 4년차 백엔드 개발자야"
            ),
        ],
        "blueprint": BlueprintData(
            goal=None,
            why=None,
            timeline=None,
            obstacles=None,
            resources=None,
            milestones=[],
            fieldScores=FieldScores(),
            readinessTips=[],
            successTips=[],
        ),
        "user_intent": None,
        "analysis_status": "starting",
    }

    print("=" * 60)
    print("🧪 v2 Quality Test")
    print("=" * 60)
    print(f"📝 Input: {state['messages'][-1].content}")
    print("-" * 60)

    start = time.time()

    # Run graph and capture final state
    final_state = None
    async for event in graph.astream_events(state, version="v2"):
        if event["event"] == "on_chain_end" and event.get("name") == "process":
            final_state = event["data"].get("output", {})

    elapsed = time.time() - start

    print(f"\n⏱️  Latency: {elapsed:.2f}s")
    print("-" * 60)

    if final_state:
        # Show response
        if "messages" in final_state and final_state["messages"]:
            response = final_state["messages"][-1].content
            print(f"\n💬 AI Response:\n{response}")

        # Show blueprint updates
        if "blueprint" in final_state:
            bp = final_state["blueprint"]
            print("\n📋 Blueprint:")
            print(f"   Goal: {bp.goal}")
            print(f"   Why: {bp.why}")
            print(f"   Timeline: {bp.timeline}")
            print(f"   Scores: goal={bp.fieldScores.goal}, why={bp.fieldScores.why}")
            if bp.readinessTips:
                print(f"   Tips: {bp.readinessTips}")
    else:
        print("❌ No output received")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_v2_quality())

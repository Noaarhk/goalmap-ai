#!/usr/bin/env python3
"""
Database seeding script for development environment.

Usage:
    uv run python scripts/seed_db.py

This script populates the development database with sample data
for testing and development purposes.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import async_session_factory
from app.models.conversation import Conversation
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.roadmap_repo import RoadmapRepository
from sqlalchemy.ext.asyncio import AsyncSession

# Sample Data
SAMPLE_USER_ID = "dev-user-001"

SAMPLE_CONVERSATIONS = [
    {
        "title": "Career Change Journey",
        "blueprint": {
            "goal": "Transition from Frontend to Backend Engineer",
            "why": "Passion for system design and better career prospects",
            "timeline": "6 months",
            "obstacles": "Limited backend experience, current job demands",
            "resources": "4 years frontend experience, online courses budget, mentor",
            "field_scores": {"goal": 90, "why": 85, "timeline": 70},
        },
    },
    {
        "title": "Learning Python",
        "blueprint": {
            "goal": "Become proficient in Python programming",
            "why": "To build AI applications and automation tools",
            "timeline": "3 months",
            "obstacles": "Limited time after work",
            "resources": "Laptop, internet, official documentation",
            "field_scores": {"goal": 80, "why": 75, "timeline": 60},
        },
    },
    {
        "title": "Fitness Goal",
        "blueprint": {
            "goal": "Run a marathon",
            "why": "Personal challenge and health improvement",
            "timeline": "1 year",
            "obstacles": "No running experience, busy schedule",
            "resources": "Running shoes, local park, fitness tracker",
            "field_scores": {"goal": 70, "why": 80, "timeline": 50},
        },
    },
]

SAMPLE_ROADMAP = {
    "title": "Backend Engineer Roadmap",
    "goal": "Become a Backend Engineer",
    "milestones": [
        {
            "id": str(uuid4()),
            "label": "Python Fundamentals",
            "type": "milestone",
            "order": 0,
            "actions": [
                {
                    "id": str(uuid4()),
                    "label": "Learn syntax and data types",
                    "type": "action",
                },
                {"id": str(uuid4()), "label": "Master OOP concepts", "type": "action"},
                {
                    "id": str(uuid4()),
                    "label": "Practice with exercises",
                    "type": "action",
                },
            ],
        },
        {
            "id": str(uuid4()),
            "label": "Web Framework",
            "type": "milestone",
            "order": 1,
            "actions": [
                {"id": str(uuid4()), "label": "Learn FastAPI basics", "type": "action"},
                {"id": str(uuid4()), "label": "Build REST API", "type": "action"},
                {"id": str(uuid4()), "label": "Add authentication", "type": "action"},
            ],
        },
        {
            "id": str(uuid4()),
            "label": "Database Skills",
            "type": "milestone",
            "order": 2,
            "actions": [
                {
                    "id": str(uuid4()),
                    "label": "Learn SQL fundamentals",
                    "type": "action",
                },
                {
                    "id": str(uuid4()),
                    "label": "Practice with PostgreSQL",
                    "type": "action",
                },
                {"id": str(uuid4()), "label": "Learn SQLAlchemy ORM", "type": "action"},
            ],
        },
    ],
}


async def seed_conversations(session: AsyncSession) -> list[Conversation]:
    """Seed sample conversations with blueprints."""
    repo = ConversationRepository(session)
    conversations = []

    for conv_data in SAMPLE_CONVERSATIONS:
        conv = Conversation(
            user_id=SAMPLE_USER_ID,
            title=conv_data["title"],
        )
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        # Add blueprint
        await repo.update_blueprint(conv.id, conv_data["blueprint"])
        conversations.append(await repo.get(conv.id))
        print(f"  ✓ Created conversation: {conv_data['title']}")

    return conversations


async def seed_roadmap(session: AsyncSession, conversation_id: str):
    """Seed a sample roadmap."""
    repo = RoadmapRepository(session)

    roadmap = await repo.create_with_nodes(
        user_id=SAMPLE_USER_ID,
        title=SAMPLE_ROADMAP["title"],
        goal=SAMPLE_ROADMAP["goal"],
        milestones_data=SAMPLE_ROADMAP["milestones"],
        conversation_id=conversation_id,
    )
    print(f"  ✓ Created roadmap: {SAMPLE_ROADMAP['title']}")
    return roadmap


async def seed_database():
    """Main seeding function."""
    print("\n🌱 Starting database seeding...")
    print("=" * 50)

    async with async_session_factory() as session:
        # Check if data already exists
        existing = await session.execute(
            "SELECT COUNT(*) FROM conversations WHERE user_id = :uid",
            {"uid": SAMPLE_USER_ID},
        )
        count = existing.scalar()

        if count > 0:
            print(f"\n⚠️  Data already exists for user {SAMPLE_USER_ID}")
            print("   Skipping seeding to avoid duplicates.")
            print("   To reset, run: DROP TABLE conversations CASCADE;")
            return

        print("\n📝 Seeding conversations...")
        conversations = await seed_conversations(session)

        print("\n🗺️  Seeding roadmap...")
        await seed_roadmap(session, conversations[0].id)

        print("\n" + "=" * 50)
        print("✅ Seeding complete!")
        print(f"   User ID: {SAMPLE_USER_ID}")
        print(f"   Conversations: {len(conversations)}")
        print("   Roadmaps: 1")


if __name__ == "__main__":
    asyncio.run(seed_database())

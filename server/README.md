# GoalMap AI Server

FastAPI backend for GoalMap AI, powered by LangChain pipelines and PostgreSQL.

## Quick Start

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run migrations
uv run alembic upgrade head

# Start server
uv run uvicorn app.main:app --reload
```

Server runs at http://localhost:8000 (API docs at `/docs`)

## Project Structure

```
server/
├── app/
│   ├── agents/           # LangChain pipelines
│   │   ├── discovery/    # Goal discovery (analyze_turn → generate_chat)
│   │   └── roadmap/      # Roadmap gen (skeleton → actions → direct_actions)
│   ├── api/
│   │   └── routes/       # REST endpoints
│   │       ├── discovery.py
│   │       ├── conversations.py
│   │       ├── roadmaps.py
│   │       └── checkins.py
│   ├── core/             # Config, DB, exceptions
│   ├── models/           # SQLAlchemy models
│   ├── repositories/     # Data access layer
│   ├── schemas/          # Pydantic schemas (api/, events/, llm/)
│   └── services/         # Business logic
├── migrations/           # Alembic migrations
└── tests/                # Pytest tests
```

## Models

| Model | Description |
|-------|-------------|
| `Conversation` | Discovery session with user |
| `Message` | Chat messages in conversation |
| `Blueprint` | Extracted goals & context from discovery |
| `Roadmap` | Generated roadmap from blueprint |
| `Node` | Milestones and actions in roadmap |
| `CheckIn` | User progress check-ins |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/discovery/chat` | Send message to discovery agent |
| `GET /api/v1/conversations/{id}` | Get conversation with messages |
| `POST /api/v1/roadmaps/generate` | Generate roadmap from blueprint |
| `GET /api/v1/roadmaps/{id}` | Get roadmap with nodes |
| `POST /api/v1/checkins` | Create progress check-in |

## Environment Variables

```env
# Required
GEMINI_API_KEY=your_key

# PostgreSQL
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=goalmap
POSTGRES_PORT=5432

# Optional: Supabase Auth
SUPABASE_URL=...
SUPABASE_SECRET_KEY=...
SUPABASE_JWT_SECRET=...

# Optional: Langfuse
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
```

## Database

```bash
# Run migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Rollback
uv run alembic downgrade -1
```

## Testing

```bash
uv run pytest
uv run pytest -v                    # verbose
uv run pytest tests/integration/    # integration only
```

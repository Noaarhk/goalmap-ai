# GoalMap AI

GoalMap AI is an intelligent application that transforms vague aspirations into actionable roadmaps using AI-powered conversational discovery. Built with LangGraph agents and React Flow visualization.

## 🌟 Key Features

- **AI-Powered Discovery**: Conversational agent that extracts goals, context, and uncertainties from natural dialogue
- **3-Tier Roadmap Generation**: Automatically generates skeleton → milestones → actionable tasks
- **Interactive Visualization**: Dynamic node-based roadmaps powered by React Flow with Dagre auto-layout
- **Progress Tracking**: Check-in system with readiness scoring and progress gauges
- **Observability**: Full LLM tracing via Langfuse integration

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 19, TypeScript, Vite
- **State Management**: Zustand
- **Visualization**: React Flow, Dagre
- **Auth**: Supabase Auth
- **Styling**: CSS Modules, Lucide Icons
- **Quality**: Biome (Linting & Formatting)

### Backend
- **Framework**: FastAPI, Python 3.12+
- **AI Orchestration**: LangGraph, LangChain
- **LLM**: Google Gemini (via langchain-google-genai)
- **Database**: PostgreSQL 15, SQLAlchemy 2.0, Alembic
- **Package Manager**: uv
- **Observability**: Langfuse

### Infrastructure
- **Containerization**: Docker Compose
- **Database**: PostgreSQL 15 (Alpine)

## 🚀 Getting Started

### Prerequisites

- Node.js v18+
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker & Docker Compose (optional, for containerized setup)
- Google Gemini API Key
- Supabase project (for auth)

### Environment Variables

Create a `.env.local` file in the root directory:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key
VITE_GEMINI_API_KEY=your_gemini_api_key

# Supabase Auth
SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_supabase_secret_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

# Optional: Langfuse (LLM Observability)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key

# PostgreSQL (defaults work with docker-compose)
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=goalmap
POSTGRES_PORT=5432
```

### Option 1: Docker Compose (Recommended)

```bash
# Start all services (server + postgres)
docker compose up -d

# Run database migrations
cd server && uv run alembic upgrade head

# Start frontend
npm install
npm run dev
```

### Option 2: Manual Setup

**1. Database**
```bash
# Start PostgreSQL (or use existing instance)
docker compose up postgres -d
```

**2. Backend**
```bash
cd server

# Install uv if not installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies & run migrations
uv sync
uv run alembic upgrade head

# Start server
uv run uvicorn app.main:app --reload
```

**3. Frontend**
```bash
# From project root
npm install
npm run dev
```

### Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Project Structure

```
goalmap-ai/
├── src/                    # Frontend (React)
│   ├── app/                # App layout & routing
│   ├── components/         # Shared UI components
│   ├── features/           # Feature modules
│   │   ├── auth/           # Authentication
│   │   ├── discovery/      # Goal discovery chat
│   │   └── visualization/  # Roadmap visualization
│   ├── services/           # API client, Supabase
│   ├── stores/             # Zustand state management
│   └── types/              # TypeScript definitions
│
├── server/                 # Backend (FastAPI)
│   ├── app/
│   │   ├── agents/         # LangGraph agents
│   │   │   ├── discovery/  # Conversational goal discovery
│   │   │   └── roadmap/    # 3-tier roadmap generation
│   │   ├── api/            # REST API routes
│   │   ├── core/           # Config, DB, exceptions
│   │   ├── models/         # SQLAlchemy models
│   │   ├── repositories/   # Data access layer
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── migrations/         # Alembic migrations
│   └── tests/              # Pytest tests
│
└── docker-compose.yml      # Container orchestration
```

## 🤖 Agent Architecture

### Discovery Agent
Pipeline: `START → analyze_turn → generate_chat → END`
- Extracts goals, context, and uncertainties from conversation
- Maintains conversation state with LangGraph checkpointing

### Roadmap Agent
Pipeline: `START → plan_skeleton → generate_actions → generate_direct_actions → END`
- Generates hierarchical roadmap structure
- Creates milestone-level and action-level tasks

## 🧪 Testing

```bash
cd server
uv run pytest
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

from app.api.routes import conversations, discovery, roadmaps
from app.core.config import settings
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LangGraph-powered backend for GoalMap AI",
    version=settings.VERSION,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
    if settings.BACKEND_CORS_ORIGINS
    else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    discovery.router,
    prefix=settings.API_V1_STR,
    tags=["discovery"],
)
app.include_router(
    conversations.router,
    prefix=f"{settings.API_V1_STR}/conversations",
    tags=["conversations"],
)
app.include_router(
    roadmaps.router,
    prefix=f"{settings.API_V1_STR}/roadmaps",
    tags=["roadmaps"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

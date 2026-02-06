from app.api.routes import checkins, conversations, discovery, roadmaps
from app.core.config import settings
from app.core.exceptions import AppException
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LangGraph-powered backend for GoalMap AI",
    version=settings.VERSION,
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "detail": exc.detail,
            "code": exc.__class__.__name__,
        },
        headers=exc.headers,
    )


# CORS configuration
_cors_origins = (
    [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
    if settings.BACKEND_CORS_ORIGINS
    else ["*"] if settings.is_dev else []
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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
app.include_router(
    checkins.router,
    prefix=settings.API_V1_STR,
    tags=["checkins"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

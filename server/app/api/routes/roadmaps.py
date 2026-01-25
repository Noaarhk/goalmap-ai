from uuid import UUID

from app.api.dependencies import CurrentUser, get_current_user, get_optional_user
from app.core.database import get_db
from app.repositories.roadmap_repo import RoadmapRepository
from app.schemas.api_schemas import RoadmapCreate, RoadmapResponse, RoadmapUpdate
from app.schemas.roadmap import GenerateRoadmapRequest
from app.services.roadmap_service import RoadmapStreamService
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
async def create_roadmap(
    payload: RoadmapCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = RoadmapRepository(db)
    roadmap = await repo.create(
        user_id=user.user_id,
        title=payload.title,
        goal=payload.goal,
        milestones=payload.milestones,
        conversation_id=payload.conversation_id,
    )
    return roadmap


@router.get("/", response_model=list[RoadmapResponse])
async def get_roadmaps(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    repo = RoadmapRepository(db)
    return await repo.get_by_user_id(user.user_id)


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(
    roadmap_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = RoadmapRepository(db)
    roadmap = await repo.get(roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    if roadmap.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return roadmap


@router.put("/{roadmap_id}", response_model=RoadmapResponse)
async def update_roadmap(
    roadmap_id: UUID,
    payload: RoadmapUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = RoadmapRepository(db)
    roadmap = await repo.get(roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    if roadmap.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = payload.model_dump(exclude_unset=True)
    roadmap = await repo.update(roadmap, **update_data)
    return roadmap


@router.delete("/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roadmap(
    roadmap_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = RoadmapRepository(db)
    roadmap = await repo.get(roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    if roadmap.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await repo.delete(roadmap)


@router.post("/stream")
async def stream_roadmap(
    request: GenerateRoadmapRequest,
    user: CurrentUser | None = Depends(get_optional_user),
):
    """
    Stream Roadmap generation via SSE.

    Generates milestones and tasks progressively.
    """
    user_id = user.user_id if user else None
    return StreamingResponse(
        RoadmapStreamService.stream_roadmap(request, user_id),
        media_type="text/event-stream",
    )

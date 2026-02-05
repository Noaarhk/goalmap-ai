from uuid import UUID

from app.api.dependencies import (
    CurrentUser,
    get_current_user,
    get_roadmap_repo,
    get_roadmap_service,
)

# Removed get_db and AsyncSession imports
from app.repositories.roadmap_repo import RoadmapRepository
from app.schemas.api.roadmaps import (
    GenerateRoadmapRequest,
    RoadmapCreate,
    RoadmapResponse,
    RoadmapUpdate,
)
from app.services.roadmap_service import RoadmapStreamService
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.post("/", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
async def create_roadmap(
    payload: RoadmapCreate,
    user: CurrentUser = Depends(get_current_user),
    repo: RoadmapRepository = Depends(get_roadmap_repo),
):
    roadmap = await repo.create_with_nodes(
        user_id=user.user_id,
        title=payload.title,
        goal=payload.goal,
        milestones_data=payload.milestones,
        conversation_id=payload.conversation_id,
    )
    return roadmap


@router.get("/", response_model=list[RoadmapResponse])
async def get_roadmaps(
    user: CurrentUser = Depends(get_current_user),
    repo: RoadmapRepository = Depends(get_roadmap_repo),
    skip: int = 0,
    limit: int = 100,
):
    return await repo.get_by_user_id(user.user_id)


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(
    roadmap_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    repo: RoadmapRepository = Depends(get_roadmap_repo),
):
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
    repo: RoadmapRepository = Depends(get_roadmap_repo),
):
    roadmap = await repo.get(roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    if roadmap.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = payload.model_dump(exclude_unset=True)

    # Handle milestones update separately (replace all nodes)
    milestones_data = update_data.pop("milestones", None)

    if update_data:
        roadmap = await repo.update(roadmap, **update_data)

    if milestones_data is not None:
        # Full replacement of nodes logic would go here
        # For now, we will re-implement this in the repository or service
        # But to avoid breaking, we should probably implement a replace_nodes method
        roadmap = await repo.update_with_nodes(roadmap.id, milestones_data)

    return roadmap


@router.delete("/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roadmap(
    roadmap_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    repo: RoadmapRepository = Depends(get_roadmap_repo),
):
    roadmap = await repo.get(roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    if roadmap.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await repo.delete(roadmap)


@router.post("/stream")
async def stream_roadmap(
    request: GenerateRoadmapRequest,
    user: CurrentUser = Depends(get_current_user),
    service: RoadmapStreamService = Depends(get_roadmap_service),
):
    """
    Stream Roadmap generation via SSE.

    Generates milestones and tasks progressively.
    """
    user_id = user.user_id if user else None
    return StreamingResponse(
        service.stream_roadmap(request, user_id),
        media_type="text/event-stream",
    )

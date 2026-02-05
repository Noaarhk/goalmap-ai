from uuid import UUID

from app.api.dependencies import (
    CurrentUser,
    get_current_user,
    get_roadmap_service,
    get_uow,
)
from app.core.exceptions import AppException, NotFoundException
from app.core.uow import AsyncUnitOfWork
from app.schemas.api.roadmaps import (
    GenerateRoadmapRequest,
    ResumeRoadmapRequest,
    RoadmapCreate,
    RoadmapResponse,
    RoadmapUpdate,
)
from app.services.roadmap_service import RoadmapStreamService
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.post("/", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
async def create_roadmap(
    payload: RoadmapCreate,
    user: CurrentUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        roadmap = await uow.roadmaps.create_with_nodes(
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
    uow: AsyncUnitOfWork = Depends(get_uow),
    skip: int = 0,
    limit: int = 100,
):
    async with uow:
        return await uow.roadmaps.get_by_user_id(user.user_id)


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(
    roadmap_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        roadmap = await uow.roadmaps.get(roadmap_id)
        if not roadmap:
            raise NotFoundException("Roadmap not found")
        if roadmap.user_id != user.user_id:
            raise AppException("Not authorized", status_code=status.HTTP_403_FORBIDDEN)
        return roadmap


@router.put("/{roadmap_id}", response_model=RoadmapResponse)
async def update_roadmap(
    roadmap_id: UUID,
    payload: RoadmapUpdate,
    user: CurrentUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        roadmap = await uow.roadmaps.get(roadmap_id)
        if not roadmap:
            raise NotFoundException("Roadmap not found")
        if roadmap.user_id != user.user_id:
            raise AppException("Not authorized", status_code=status.HTTP_403_FORBIDDEN)

        update_data = payload.model_dump(exclude_unset=True)

        # Handle milestones update separately (replace all nodes)
        milestones_data = update_data.pop("milestones", None)

        if update_data:
            roadmap = await uow.roadmaps.update(roadmap, **update_data)

        if milestones_data is not None:
            roadmap = await uow.roadmaps.update_with_nodes(roadmap.id, milestones_data)

        return roadmap


@router.delete("/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roadmap(
    roadmap_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        roadmap = await uow.roadmaps.get(roadmap_id)
        if not roadmap:
            raise NotFoundException("Roadmap not found")
        if roadmap.user_id != user.user_id:
            raise AppException("Not authorized", status_code=status.HTTP_403_FORBIDDEN)

        await uow.roadmaps.delete(roadmap)


@router.post("/stream")
async def stream_roadmap(
    request: GenerateRoadmapRequest,
    user: CurrentUser = Depends(get_current_user),
    service: RoadmapStreamService = Depends(get_roadmap_service),
):
    """
    Legacy: Stream full Roadmap generation via SSE (no HIL).

    For backward compatibility. Use /stream/skeleton + /stream/actions for HIL.
    """
    return StreamingResponse(
        service.stream_roadmap(request, user.user_id),
        media_type="text/event-stream",
    )


@router.post("/stream/skeleton")
async def stream_skeleton(
    request: GenerateRoadmapRequest,
    user: CurrentUser = Depends(get_current_user),
    service: RoadmapStreamService = Depends(get_roadmap_service),
):
    """
    HIL Step 1: Generate roadmap skeleton (milestones only).

    Returns skeleton structure for user review.
    The response includes a thread_id for resuming with /stream/actions.
    """
    return StreamingResponse(
        service.stream_skeleton(request, user.user_id),
        media_type="text/event-stream",
    )


@router.post("/stream/actions")
async def stream_actions(
    request: ResumeRoadmapRequest,
    user: CurrentUser = Depends(get_current_user),
    service: RoadmapStreamService = Depends(get_roadmap_service),
):
    """
    HIL Step 2: Resume and generate all actions.

    Call after user has approved the skeleton from /stream/skeleton.
    Requires thread_id from the skeleton response.
    
    If modified_milestones is provided, generates actions based on user's edits.
    Otherwise, resumes from checkpoint with original skeleton.
    """
    # Build GenerateRoadmapRequest for persistence if fields provided
    persist_request = None
    if request.goal:
        persist_request = GenerateRoadmapRequest(
            conversation_id=request.conversation_id or "",
            goal=request.goal,
            why=request.why or "",
            timeline=request.timeline,
            obstacles=request.obstacles,
            resources=request.resources,
        )

    return StreamingResponse(
        service.stream_actions(
            request.thread_id,
            user.user_id,
            persist_request,
            request.modified_milestones,
        ),
        media_type="text/event-stream",
    )

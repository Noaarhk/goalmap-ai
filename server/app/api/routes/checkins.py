from app.api.dependencies import get_uow
from app.core.uow import AsyncUnitOfWork
from app.schemas.api.checkins import (
    CheckInAnalyzeRequest,
    CheckInAnalyzeResponse,
    CheckInConfirmRequest,
    CheckInConfirmResponse,
)
from app.services import checkin_service
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/checkins", tags=["checkins"])


@router.post("/analyze", response_model=CheckInAnalyzeResponse)
async def analyze_checkin(
    request: CheckInAnalyzeRequest,
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    """
    Analyze a user's check-in text and propose updates to roadmap nodes.
    Returns the check-in ID and list of proposed updates for confirmation.
    """
    try:
        checkin, updates = await checkin_service.analyze_checkin(
            roadmap_id=request.roadmap_id,
            user_input=request.user_input,
            uow=uow,
        )
        return CheckInAnalyzeResponse(
            checkin_id=checkin.id,
            proposed_updates=updates,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/confirm", response_model=CheckInConfirmResponse)
async def confirm_checkin(
    request: CheckInConfirmRequest,
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    """
    Confirm and apply the proposed updates from a check-in.
    Optionally accepts modified updates from the frontend.
    """
    try:
        updated_nodes = await checkin_service.confirm_checkin(
            checkin_id=request.checkin_id,
            uow=uow,
            custom_updates=request.updates,
        )
        return CheckInConfirmResponse(
            success=True,
            updated_nodes=updated_nodes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confirmation failed: {str(e)}")


@router.post("/{checkin_id}/reject")
async def reject_checkin(
    checkin_id: str,
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    """
    Reject a pending check-in without applying updates.
    """
    from uuid import UUID

    try:
        await checkin_service.reject_checkin(
            checkin_id=UUID(checkin_id),
            uow=uow,
        )
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

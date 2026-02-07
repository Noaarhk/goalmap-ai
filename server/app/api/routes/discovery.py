"""
Discovery Routes

Streaming endpoints for Discovery Agent conversations.
Uses V3 pipeline: Response First, Background Analysis.
"""

import logging

from app.api.dependencies import (
    CurrentUser,
    get_discovery_service,
    get_optional_user,
)
from app.schemas.api.chat import ChatRequest
from app.services.discovery_service import DiscoveryStreamService
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    user: CurrentUser | None = Depends(get_optional_user),
    service: DiscoveryStreamService = Depends(get_discovery_service),
):
    """
    Stream Discovery Agent chat responses via SSE.

    Features:
    - Immediate token streaming (no blocking)
    - Background analysis runs AFTER user sees full response
    - Blueprint update is non-blocking
    - Uncertainty detection and tracking
    """
    logger.info(
        f"Incoming chat request: chat_id={request.chat_id} message={request.message[:50]}..."
    )
    user_id = user.user_id if user else None
    return StreamingResponse(
        service.stream_chat(request, user_id),
        media_type="text/event-stream",
    )

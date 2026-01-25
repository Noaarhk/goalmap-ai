"""
Discovery Routes

Streaming endpoints for Discovery Agent conversations.
"""

import logging

from app.api.dependencies import CurrentUser, get_optional_user
from app.schemas.discovery import ChatRequest
from app.services.discovery_service import DiscoveryStreamService
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    user: CurrentUser | None = Depends(get_optional_user),
):
    """
    Stream Discovery Agent chat responses via SSE.

    Supports both authenticated and anonymous users.
    """
    logger.info(
        f"Incoming chat request: chat_id={request.chat_id} message={request.message[:50]}..."
    )
    user_id = user.user_id if user else None
    return StreamingResponse(
        DiscoveryStreamService.stream_chat(request, user_id),
        media_type="text/event-stream",
    )

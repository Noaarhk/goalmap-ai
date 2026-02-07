"""
Discovery Streaming Service - Response First, Background Analysis

Features:
- Immediate token streaming (no blocking analysis)
- Background analysis runs AFTER user sees full response
- Blueprint update is non-blocking
- Uncertainty detection and tracking
"""

import logging
import uuid
from typing import AsyncGenerator

from app.agents.discovery.pipeline import stream_response, analyze_response_background
from app.core.uow import AsyncUnitOfWork
from app.schemas.api.chat import BlueprintData, ChatRequest
from app.schemas.events.base import ErrorEventData, StatusEventData, TokenEventData
from app.schemas.events.discovery import BlueprintUpdateEventData
from app.services.langfuse import get_langfuse_handler
from langchain_core.messages import AIMessage, HumanMessage

logger = logging.getLogger(__name__)


class DiscoveryStreamService:
    """Service for streaming Discovery Agent responses."""

    def __init__(self, uow: AsyncUnitOfWork):
        self.uow = uow

    async def stream_chat(
        self,
        request: ChatRequest,
        user_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response first, then analyze in background.

        Flow:
        1. Immediately start streaming response tokens
        2. After streaming complete, run background analysis
        3. Emit blueprint_update event when analysis is done
        """
        # 1. Prepare messages
        messages = []
        for msg in request.history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=request.message))

        # 2. Get or create blueprint
        blueprint = request.current_blueprint or BlueprintData()

        try:
            # Setup Langfuse
            effective_user_id = user_id or "anonymous"
            tags = ["authenticated"] if user_id else ["anonymous"]
            if user_id:
                tags.append("free")

            thread_id = (
                f"discovery_{effective_user_id}_{request.chat_id}"
                if request.chat_id
                else f"discovery_{effective_user_id}"
            )

            langfuse_handler = get_langfuse_handler(
                user_id=effective_user_id, session_id=thread_id, tags=tags
            )
            callbacks = [langfuse_handler] if langfuse_handler else []

            # Persist user message
            if user_id and request.chat_id:
                await self._persist_user_message(request.chat_id, request.message)

            # --- Step 1: Stream response immediately ---
            yield self._status_event("generating")

            full_response = ""
            run_id = str(uuid.uuid4())

            async for token in stream_response(messages, blueprint, callbacks):
                full_response += token
                yield self._token_event(token, run_id)

            # Persist assistant message immediately after streaming
            if user_id and request.chat_id and full_response:
                async with self.uow as uow:
                    await uow.conversations.append_message(
                        uuid.UUID(request.chat_id),
                        role="assistant",
                        content=full_response,
                    )

            # --- Step 2: Background analysis ---
            yield self._status_event("analyzing")

            updated_blueprint = await analyze_response_background(
                user_message=request.message,
                assistant_response=full_response,
                blueprint=blueprint,
                callbacks=callbacks,
            )

            # Emit blueprint update
            yield self._blueprint_event(updated_blueprint)

            # Persist blueprint
            if user_id and request.chat_id:
                await self._persist_blueprint(request.chat_id, updated_blueprint)

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            error_data = ErrorEventData(
                code="internal_error",
                message="시스템 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            )
            yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"

    async def _persist_user_message(self, chat_id: str, message: str) -> None:
        """Persist user message to database."""
        try:
            chat_uuid = uuid.UUID(chat_id)
            async with self.uow as uow:
                await uow.conversations.append_message(
                    chat_uuid, role="user", content=message
                )
        except Exception as e:
            logger.error(f"Failed to persist user message: {e}")

    async def _persist_blueprint(self, chat_id: str, blueprint: BlueprintData) -> None:
        """Persist blueprint update to database."""
        try:
            chat_uuid = uuid.UUID(chat_id)
            bp_dict = blueprint.model_dump(exclude_none=True)
            async with self.uow as uow:
                await uow.conversations.update_blueprint(chat_uuid, bp_dict)
        except Exception as e:
            logger.error(f"Failed to persist blueprint: {e}")

    @staticmethod
    def _status_event(node: str) -> str:
        """Create SSE status event."""
        data = StatusEventData(message=f"Process: {node}", node=node)
        return f"event: status\ndata: {data.model_dump_json()}\n\n"

    @staticmethod
    def _token_event(text: str, run_id: str) -> str:
        """Create SSE token event."""
        data = TokenEventData(text=text, run_id=run_id)
        return f"event: token\ndata: {data.model_dump_json()}\n\n"

    @staticmethod
    def _blueprint_event(blueprint: BlueprintData) -> str:
        """Create SSE blueprint update event."""
        bp_dict = blueprint.model_dump(exclude_none=True)
        data = BlueprintUpdateEventData(**bp_dict)
        return f"event: blueprint_update\ndata: {data.model_dump_json()}\n\n"

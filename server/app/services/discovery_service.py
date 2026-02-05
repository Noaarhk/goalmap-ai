"""
Discovery Streaming Service

Handles the business logic for Discovery Agent streaming:
- Graph execution with LangGraph
- SSE event generation
- Message persistence
- Langfuse callback integration
"""

import logging
import uuid
from typing import AsyncGenerator

from app.agents.discovery.graph import get_graph as get_discovery_graph

# Removed async_session_factory
from app.core.graph_manager import GraphManager
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.api.chat import ChatRequest
from app.schemas.events.base import ErrorEventData, StatusEventData, TokenEventData
from app.schemas.events.discovery import BlueprintUpdateEventData
from app.services.langfuse import get_langfuse_handler
from langchain_core.messages import AIMessage, HumanMessage

logger = logging.getLogger(__name__)

# Initialize Discovery Graph Manager
discovery_manager = GraphManager(get_discovery_graph, "discovery")


class DiscoveryStreamService:
    """Service for streaming Discovery Agent responses."""

    def __init__(self, repo: ConversationRepository, graph_manager: GraphManager):
        self.repo = repo
        self.graph_manager = graph_manager

    async def stream_chat(
        self,
        request: ChatRequest,
        user_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Execute discovery graph and yield SSE events.

        Args:
            request: Chat request with message, history, and blueprint
            user_id: Optional authenticated user ID

        Yields:
            SSE formatted event strings
        """
        # 1. Prepare Initial State
        messages = []
        for msg in request.history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=request.message))

        initial_state = {
            "messages": messages,
            "blueprint": request.current_blueprint or {},
            "user_intent": None,
            "analysis_status": "starting",
        }

        # Streaming state
        stream_buffer = ""
        is_streaming_response = False

        try:
            # Determine identification info for Langfuse & Thread
            effective_user_id = user_id or "anonymous"
            tags = ["authenticated"] if user_id else ["anonymous"]
            if user_id:
                tags.append("free")

            # User-specific thread for session persistence
            if request.chat_id:
                thread_id = f"discovery_{effective_user_id}_{request.chat_id}"
            else:
                thread_id = f"discovery_{effective_user_id}"

            # Setup Langfuse Callbacks
            langfuse_handler = get_langfuse_handler(
                user_id=effective_user_id, session_id=thread_id, tags=tags
            )
            callbacks = [langfuse_handler] if langfuse_handler else []

            # Persist user message
            if user_id and request.chat_id:
                await self._persist_user_message(request.chat_id, request.message)

            # Accumulator for full assistant response
            full_assistant_response = ""

            async for event in self.graph_manager.stream_events(
                initial_state, thread_id, callbacks=callbacks
            ):
                event_type = event["event"]

                # --- Stream Tokens ---
                if event_type == "on_chat_model_stream":
                    result = await self._handle_token_stream(
                        event,
                        stream_buffer,
                        is_streaming_response,
                    )
                    if result:
                        content, stream_buffer, is_streaming_response, sse_event = (
                            result
                        )
                        if content:
                            full_assistant_response += content
                        if sse_event:
                            yield sse_event

                # --- Stream Status ---
                elif event_type == "on_chain_start":
                    sse_event = self._handle_chain_start(event)
                    if sse_event:
                        yield sse_event

                # --- Stream Updates ---
                elif event_type == "on_chain_end":
                    sse_event = await self._handle_chain_end(
                        event, user_id, request.chat_id
                    )
                    if sse_event:
                        yield sse_event

            # Persist assistant message at end
            if user_id and request.chat_id and full_assistant_response:
                await self._persist_assistant_message(
                    request.chat_id, full_assistant_response
                )

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
            # Use injected repository
            await self.repo.append_message(chat_uuid, role="user", content=message)
        except ValueError:
            logger.warning(f"Invalid chat_id format: {chat_id}")
        except Exception as e:
            logger.error(f"Failed to persist user message: {e}")

    async def _persist_assistant_message(self, chat_id: str, message: str) -> None:
        """Persist assistant message to database."""
        try:
            chat_uuid = uuid.UUID(chat_id)
            # Use injected repository
            await self.repo.append_message(chat_uuid, role="assistant", content=message)
        except ValueError:
            pass  # Already logged warning above
        except Exception as e:
            logger.error(f"Failed to persist assistant message: {e}")

    @staticmethod
    async def _handle_token_stream(
        event: dict,
        stream_buffer: str,
        is_streaming_response: bool,
    ) -> tuple[str, str, bool, str | None] | None:
        """
        Handle token streaming events.

        Returns:
            Tuple of (content, updated_buffer, updated_streaming_flag, sse_event) or None
        """
        tags = event.get("tags", [])
        if not (
            "generate_response" in tags
            or "single_turn_handler" in tags
            or "generate_chat" in tags
        ):
            return None

        chunk = event["data"]["chunk"]
        content = chunk.content

        # Handle list-based content (Gemini 3 Preview fix)
        if isinstance(content, list):
            text_content = ""
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_content += part.get("text", "")
                elif hasattr(part, "text"):
                    text_content += part.text
            content = text_content

        if not content:
            return None

        # --- Pipeline: Direct streaming ---
        if "generate_chat" in tags:
            token_data = TokenEventData(text=content, run_id=event["run_id"])
            return (
                content,
                stream_buffer,
                is_streaming_response,
                f"event: token\ndata: {token_data.model_dump_json()}\n\n",
            )

        # --- Single Turn: Parse JSON response ---
        if "single_turn_handler" in tags:
            return DiscoveryStreamService._parse_response(
                content, stream_buffer, is_streaming_response, event["run_id"]
            )

        return None

    def _parse_response(
        self,
        content: str,
        stream_buffer: str,
        is_streaming_response: bool,
        run_id: str,
    ) -> tuple[str, str, bool, str | None]:
        """Parse JSON response and extract text."""
        if not is_streaming_response:
            stream_buffer += content
            START_TOKEN = '"response": "'
            if START_TOKEN in stream_buffer:
                is_streaming_response = True
                start_idx = stream_buffer.find(START_TOKEN) + len(START_TOKEN)
                content = stream_buffer[start_idx:]
                stream_buffer = ""
            else:
                if len(stream_buffer) > 200:
                    stream_buffer = stream_buffer[-50:]
                return ("", stream_buffer, is_streaming_response, None)

        if is_streaming_response:
            full_chunk = stream_buffer + content
            stream_buffer = ""

            end_idx = -1
            i = 0
            while i < len(full_chunk):
                if full_chunk[i] == '"':
                    if i > 0 and full_chunk[i - 1] == "\\":
                        pass
                    else:
                        end_idx = i
                        break
                i += 1

            if end_idx != -1:
                content_to_yield = full_chunk[:end_idx]
                is_streaming_response = False
            else:
                if full_chunk.endswith("\\"):
                    stream_buffer = "\\"
                    content_to_yield = full_chunk[:-1]
                else:
                    content_to_yield = full_chunk

            # JSON unescaping
            content = content_to_yield.replace('\\"', '"').replace("\\n", "\n")

            token_data = TokenEventData(text=content, run_id=run_id)
            return (
                content,
                stream_buffer,
                is_streaming_response,
                f"event: token\ndata: {token_data.model_dump_json()}\n\n",
            )

        return ("", stream_buffer, is_streaming_response, None)

    def _handle_chain_start(self, event: dict) -> str | None:
        """Handle chain start events for status updates."""
        node_name = event["name"]
        if node_name in [
            "analyze_input",
            "extract_goal",
            "extract_tactics",
            "generate_response",
            "process",
            "analyze_turn",
            "generate_chat",
        ]:
            status_data = StatusEventData(
                message=f"Process: {node_name}", node=node_name
            )
            return f"event: status\ndata: {status_data.model_dump_json()}\n\n"
        return None

    async def _handle_chain_end(
        self, event: dict, user_id: str | None, chat_id: str | None
    ) -> str | None:
        """Handle chain end events for blueprint updates."""
        output = event["data"].get("output")
        if not output or not isinstance(output, dict) or "blueprint" not in output:
            return None

        bp_data = output["blueprint"]
        if hasattr(bp_data, "model_dump"):
            bp_dict = bp_data.model_dump(exclude_none=True)
        else:
            bp_dict = bp_data

        update_data = BlueprintUpdateEventData(**bp_dict)
        sse_event = (
            f"event: blueprint_update\ndata: {update_data.model_dump_json()}\n\n"
        )

        # Persist blueprint update
        if user_id and chat_id:
            try:
                chat_uuid = uuid.UUID(chat_id)
                await self.repo.update_blueprint(chat_uuid, bp_dict)
            except Exception as e:
                logger.error(f"Failed to persist blueprint: {e}")

        return sse_event

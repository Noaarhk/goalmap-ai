from uuid import UUID

from app.api.dependencies import CurrentUser, get_current_user, get_uow
from app.core.exceptions import AppException, NotFoundException
from app.core.uow import AsyncUnitOfWork
from app.schemas.api.conversations import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)
from fastapi import APIRouter, Depends, status

router = APIRouter()


@router.post(
    "/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    payload: ConversationCreate,
    user: CurrentUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        # Optionally initialize with a system message or user message if provided
        # For now, just create empty or with title
        conversation = await uow.conversations.create(
            user_id=user.user_id, title=payload.title or "New Quest"
        )
        return conversation


@router.get("/", response_model=list[ConversationResponse])
async def get_conversations(
    user: CurrentUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
    skip: int = 0,
    limit: int = 100,
):
    async with uow:
        return await uow.conversations.get_by_user_with_messages_and_blueprint(
            user.user_id
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        conversation = await uow.conversations.get_with_messages_and_blueprint(
            conversation_id
        )
        if not conversation:
            raise NotFoundException("Conversation not found")
        if conversation.user_id != user.user_id:
            raise AppException("Not authorized", status_code=status.HTTP_403_FORBIDDEN)
        return conversation


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,
    user: CurrentUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        # Lazy load is sufficient for ownership check
        conversation = await uow.conversations.get(conversation_id)
        if not conversation:
            raise NotFoundException("Conversation not found")
        if conversation.user_id != user.user_id:
            raise AppException("Not authorized", status_code=status.HTTP_403_FORBIDDEN)

        update_data = payload.model_dump(exclude_unset=True)
        # Repo update method returns eager-loaded object
        conversation = await uow.conversations.update(conversation, **update_data)
        return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        # Lazy load is sufficient for delete
        conversation = await uow.conversations.get(conversation_id)
        if not conversation:
            raise NotFoundException("Conversation not found")
        if conversation.user_id != user.user_id:
            raise AppException("Not authorized", status_code=status.HTTP_403_FORBIDDEN)

        await uow.conversations.delete(conversation)

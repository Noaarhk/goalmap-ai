from uuid import UUID

from app.api.dependencies import CurrentUser, get_current_user
from app.core.database import get_db
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.api_schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post(
    "/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    payload: ConversationCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)

    # Optionally initialize with a system message or user message if provided
    # For now, just create empty or with title
    conversation = await repo.create(
        user_id=user.user_id, title=payload.title or "New Quest"
    )
    return conversation


@router.get("/", response_model=list[ConversationResponse])
async def get_conversations(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    repo = ConversationRepository(db)
    return await repo.get_by_user_with_messages_and_blueprint(user.user_id)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conversation = await repo.get_with_messages_and_blueprint(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return conversation


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    # Lazy load is sufficient for ownership check
    conversation = await repo.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = payload.model_dump(exclude_unset=True)
    # Repo update method returns eager-loaded object
    conversation = await repo.update(conversation, **update_data)
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    # Lazy load is sufficient for delete
    conversation = await repo.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await repo.delete(conversation)

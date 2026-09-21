from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth import get_current_user_id
from ai_chat.conversations.models import Conversation
from ai_chat.conversations.schemas import ConversationRead
from ai_chat.shared.db import get_session

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> list[ConversationRead]:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at)
    )
    return [ConversationRead.model_validate(row) for row in result.scalars().all()]

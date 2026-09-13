from fastapi import Depends
from supertokens_python.recipe.session import SessionContainer

from ai_chat.auth.adapter_supertokens import session_dependency


async def get_current_user_id(
    session: SessionContainer = Depends(session_dependency()),
) -> str:
    return session.get_user_id()

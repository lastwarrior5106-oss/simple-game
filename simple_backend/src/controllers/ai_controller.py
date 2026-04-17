import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models.user import User
from src.utils.security import SecurityUtils
from src.services.chat_service.graph.main_graph import run_graph, stream_graph
from src.schemas.ai import ChatRequest, ChatResponse

router = APIRouter(tags=["AI"], include_in_schema=True)


class AIController:
    router = router

    @staticmethod
    @router.post("/chat", response_model=ChatResponse)
    async def chat(
        body: ChatRequest,
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ):
        """Normal (non-streaming) endpoint. Tüm yanıtı tek seferde döndürür."""
        history = [m.model_dump() for m in body.conversation_history]

        result = await run_graph(
            user_message=body.message,
            session=session,
            conversation_history=history,
            current_user_id=current_user.id,
            current_user_role=current_user.role,
            current_team_id=current_user.team_id,
            user_coins=current_user.coins,
            user_level=current_user.level,
        )

        return ChatResponse(
            response=result["response"],
            execution_log=result["execution_log"],
        )

    @staticmethod
    @router.post("/chat/stream")
    async def chat_stream(
        body: ChatRequest,
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ):
        """
        SSE streaming endpoint.

        Event formatı:
          data: {"type": "node",  "node": "router"}
          data: {"type": "token", "content": "Merhaba"}
          data: {"type": "done",  "current_user_id": 1, "user_coins": 95, ...}
          data: {"type": "error", "message": "..."}

        Her event 'data: ' prefix'i ile gelir, çift newline ile ayrılır.
        """
        history = [m.model_dump() for m in body.conversation_history]

        async def event_generator():
            async for event in stream_graph(
                user_message=body.message,
                session=session,
                conversation_history=history,
                current_user_id=current_user.id,
                current_user_role=current_user.role,
                current_team_id=current_user.team_id,
                user_coins=current_user.coins,
                user_level=current_user.level,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
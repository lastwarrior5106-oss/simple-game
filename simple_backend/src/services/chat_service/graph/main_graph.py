"""
Ana Graph

Akış:
  router_node → orchestrator_node → responder_node

Router hata üretirse direkt responder'a gider.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.graph import StateGraph, END
from typing import AsyncGenerator

from src.services.chat_service.state.main_state import MainState
from src.services.chat_service.graph.router import router_node
from src.services.chat_service.graph.orchestrator import orchestrator_node
from src.services.chat_service.graph.responder import responder_node, stream_responder_tokens

logger = logging.getLogger(__name__)


def _should_orchestrate(state: MainState) -> str:
    if state.get("global_error"):
        logger.warning(f"[main_graph] Router hatası, responder'a atlıyor: {state['global_error']}")
        return "responder"
    if not state.get("planned_steps"):
        logger.info("[main_graph] Boş plan, responder'a atlıyor")
        return "responder"
    return "orchestrator"


def build_main_graph(session: AsyncSession) -> StateGraph:
    graph = StateGraph(MainState)

    async def _orchestrator(state: MainState) -> dict:
        return await orchestrator_node(state, session)

    graph.add_node("router", router_node)
    graph.add_node("orchestrator", _orchestrator)
    graph.add_node("responder", responder_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        _should_orchestrate,
        {
            "orchestrator": "orchestrator",
            "responder": "responder",
        },
    )

    graph.add_edge("orchestrator", "responder")
    graph.add_edge("responder", END)

    return graph.compile()


async def run_graph(
    user_message: str,
    session: AsyncSession,
    conversation_history: list[dict] | None = None,
    current_user_id: int | None = None,
    current_user_role: str | None = None,
    current_team_id: int | None = None,
    user_coins: int | None = None,
    user_level: int | None = None,
) -> dict:
    """Tek seferde çalıştırır, tüm sonucu döndürür. (Normal /chat endpoint'i için)"""
    history = conversation_history or []
    messages = history + [{"role": "user", "content": user_message}]

    initial_state: MainState = {
        "messages": messages,
        "router_context": messages[-5:],
        "planned_steps": [],
        "completed_steps": [],
        "current_step": None,
        "dependencies": {},
        "instructions": {},
        "supervisor_results": {},
        "execution_log": [],
        "current_user_id": current_user_id,
        "current_user_role": current_user_role,
        "current_team_id": current_team_id,
        "user_coins": user_coins,
        "user_level": user_level,
        "global_error": None,
        "final_response": None,
    }

    compiled_graph = build_main_graph(session)
    final_state = await compiled_graph.ainvoke(initial_state)

    return {
        "response": final_state.get("final_response", ""),
        "execution_log": final_state.get("execution_log", []),
    }


async def stream_graph(
    user_message: str,
    session: AsyncSession,
    conversation_history: list[dict] | None = None,
    current_user_id: int | None = None,
    current_user_role: str | None = None,
    current_team_id: int | None = None,
    user_coins: int | None = None,
    user_level: int | None = None,
) -> AsyncGenerator[dict, None]:
    """
    SSE endpoint'i için generator.

    Yield ettiği event tipleri:
      {"type": "node",  "node": "router"}          → node başladı
      {"type": "token", "content": "..."}           → responder LLM token'ı
      {"type": "done",  "execution_log": [...], "full_response": "..."} → bitti
      {"type": "error", "message": "..."}           → hata
    """
    history = conversation_history or []
    messages = history + [{"role": "user", "content": user_message}]

    initial_state: MainState = {
        "messages": messages,
        "router_context": messages[-5:],
        "planned_steps": [],
        "completed_steps": [],
        "current_step": None,
        "dependencies": {},
        "instructions": {},
        "supervisor_results": {},
        "execution_log": [],
        "current_user_id": current_user_id,
        "current_user_role": current_user_role,
        "current_team_id": current_team_id,
        "user_coins": user_coins,
        "user_level": user_level,
        "global_error": None,
        "final_response": None,
    }

    pre_graph = StateGraph(MainState)

    async def _orchestrator(state: MainState) -> dict:
        return await orchestrator_node(state, session)

    pre_graph.add_node("router", router_node)
    pre_graph.add_node("orchestrator", _orchestrator)

    def _should_orchestrate_pre(state: MainState) -> str:
        if state.get("global_error") or not state.get("planned_steps"):
            return "end"
        return "orchestrator"

    pre_graph.set_entry_point("router")
    pre_graph.add_conditional_edges(
        "router",
        _should_orchestrate_pre,
        {"orchestrator": "orchestrator", "end": END},
    )
    pre_graph.add_edge("orchestrator", END)

    compiled_pre = pre_graph.compile()

    try:
        yield {"type": "node", "node": "router"}
        pre_state = await compiled_pre.ainvoke(initial_state)

        if pre_state.get("planned_steps"):
            yield {"type": "node", "node": "orchestrator"}

        yield {"type": "node", "node": "responder"}

        full_response = ""
        async for token in stream_responder_tokens(pre_state):
            full_response += token
            yield {"type": "token", "content": token}

        yield {
            "type": "done",
            "execution_log": pre_state.get("execution_log", []),
            "full_response": full_response,
        }

    except Exception as e:
        logger.exception("[stream_graph] Hata")
        yield {"type": "error", "message": str(e)}
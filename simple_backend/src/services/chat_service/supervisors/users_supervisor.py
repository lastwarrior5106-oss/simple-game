"""
Users Supervisor Subgraph

Sorumluluk: create_user ve level_up işlemleri.
Ana graph ile iletişim: sadece result paketi üzerinden.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.graph import StateGraph, END

from src.services.chat_service.state.subgraph_state import UsersState, SubgraphResult
from src.services.chat_service.tools.mcp_tools import get_tools_for_supervisor
from src.services.chat_service.prompts.supervisor_prompts import USERS_SUPERVISOR_SYSTEM_PROMPT
from src.configs.chat import get_router_llm
from src.services.chat_service.supervisors.base import run_agent_loop

logger = logging.getLogger(__name__)


# ── Node'lar ──────────────────────────────────────────────────────────────────

async def execute_node(state: UsersState, session: AsyncSession) -> dict:
    """
    Ana node: LLM + tool döngüsünü çalıştırır.
    State'ten gelen context, tool parametrelerine otomatik inject edilir.
    """
    context = {
        "current_user_id": state.get("current_user_id"),
        "current_user_role": state.get("current_user_role"),
    }

    tools = await get_tools_for_supervisor("user_tools", context=context)
    llm = get_router_llm()
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = USERS_SUPERVISOR_SYSTEM_PROMPT.format(
        instruction=state["instruction"],
        current_user_id=state.get("current_user_id") or "Yok (yeni kullanıcı oluşturulacak)",
    )

    success, output, error, retry_count = await run_agent_loop(
        llm_with_tools=llm_with_tools,
        system_message=system_prompt,
        initial_human_message=state["instruction"],
        tools=tools,
    )

    result: SubgraphResult = {
        "success": success,
        "output": output if success else None,
        "error": error if not success else None,
        "retried": retry_count,
    }

    logger.info(
        f"[users_supervisor] success={success}, retried={retry_count}, "
        f"user_id={output.get('user_id') if success else None}"
    )

    return {"result": result}


def should_end(state: UsersState) -> str:
    """Result paketi doluysa bitir."""
    return END


# ── Subgraph builder ──────────────────────────────────────────────────────────

def build_users_subgraph(session: AsyncSession) -> StateGraph:
    graph = StateGraph(UsersState)

    async def _execute(state: UsersState) -> dict:
        return await execute_node(state, session)

    graph.add_node("execute", _execute)
    graph.set_entry_point("execute")
    graph.add_edge("execute", END)

    return graph.compile()


async def run_users_supervisor(
    instruction: str,
    current_user_id: int | None,
    current_user_role: str | None,
    session: AsyncSession,
) -> SubgraphResult:
    """
    Users supervisor'ı çalıştırır ve result paketi döndürür.
    Ana graph tarafından çağrılır.
    """
    subgraph = build_users_subgraph(session)

    initial_state: UsersState = {
        "instruction": instruction,
        "current_user_id": current_user_id,
        "current_user_role": current_user_role,
        "steps_done": [],
        "retry_count": 0,
        "last_error": None,
        "result": None,
        "internal_messages": [],
    }

    final_state = await subgraph.ainvoke(initial_state)
    return final_state["result"]
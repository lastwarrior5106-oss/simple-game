"""
Teams Supervisor Subgraph

Sorumluluk: create_team, join_team, leave_team, get_suggested_teams işlemleri.
Ana graph ile iletişim: sadece result paketi üzerinden.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.graph import StateGraph, END

from src.services.chat_service.state.subgraph_state import TeamsState, SubgraphResult
from src.services.chat_service.tools.mcp_tools import get_tools_for_supervisor
from src.services.chat_service.prompts.supervisor_prompts import TEAMS_SUPERVISOR_SYSTEM_PROMPT
from src.configs.chat import get_router_llm
from src.services.chat_service.supervisors.base import run_agent_loop

logger = logging.getLogger(__name__)


# ── Node'lar ──────────────────────────────────────────────────────────────────

async def execute_node(state: TeamsState, session: AsyncSession) -> dict:
    """
    Ana node: LLM + tool döngüsünü çalıştırır.
    State'ten gelen context, tool parametrelerine otomatik inject edilir.
    """
    context = {
        "current_user_id": state.get("current_user_id"),
        "current_user_role": state.get("current_user_role"),
        "current_team_id": state.get("current_team_id"),
    }

    tools = await get_tools_for_supervisor("team_tools", context=context)
    llm = get_router_llm()
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = TEAMS_SUPERVISOR_SYSTEM_PROMPT.format(
        instruction=state["instruction"],
        current_user_id=state.get("current_user_id") or "Yok",
        current_team_id=state.get("current_team_id") or "Yok",
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
        f"[teams_supervisor] success={success}, retried={retry_count}, "
        f"team_id={output.get('team_id') if success else None}"
    )

    return {"result": result}


# ── Subgraph builder ──────────────────────────────────────────────────────────

def build_teams_subgraph(session: AsyncSession) -> StateGraph:
    graph = StateGraph(TeamsState)

    async def _execute(state: TeamsState) -> dict:
        return await execute_node(state, session)

    graph.add_node("execute", _execute)
    graph.set_entry_point("execute")
    graph.add_edge("execute", END)

    return graph.compile()


async def run_teams_supervisor(
    instruction: str,
    current_user_id: int | None,
    current_user_role: str | None,
    current_team_id: int | None,
    session: AsyncSession,
) -> SubgraphResult:
    """
    Teams supervisor'ı çalıştırır ve result paketi döndürür.
    Ana graph tarafından çağrılır.
    """
    subgraph = build_teams_subgraph(session)

    initial_state: TeamsState = {
        "instruction": instruction,
        "current_user_id": current_user_id,
        "current_user_role": current_user_role,
        "current_team_id": current_team_id,
        "steps_done": [],
        "retry_count": 0,
        "last_error": None,
        "result": None,
        "internal_messages": [],
    }

    final_state = await subgraph.ainvoke(initial_state)
    return final_state["result"]
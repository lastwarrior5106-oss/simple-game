"""
Ana Router Node

Kullanıcı mesajını okur, hangi supervisor'ların çalışacağını,
sırasını ve bağımlılıklarını belirler.
"""

import json
import logging
import re
from langchain_core.messages import SystemMessage, HumanMessage

from src.services.chat_service.state.main_state import MainState
from src.services.chat_service.prompts.router_prompt import ROUTER_SYSTEM_PROMPT, ROUTER_USER_TEMPLATE
from src.configs.chat import get_router_llm

logger = logging.getLogger(__name__)

SLIDING_WINDOW = 5  # Router'ın göreceği son mesaj sayısı


def _format_recent_messages(messages: list[dict]) -> str:
    """Son N mesajı okunabilir formata çevirir."""
    recent = messages[-SLIDING_WINDOW:] if len(messages) > SLIDING_WINDOW else messages
    lines = []
    for msg in recent:
        role = "Kullanıcı" if msg["role"] == "user" else "Asistan"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines) if lines else "(Konuşma yok)"


def _format_context(state: MainState) -> str:
    """Mevcut game state'i router için özetler."""
    parts = []
    if state.get("current_user_id"):
        parts.append(f"Mevcut kullanıcı ID: {state['current_user_id']}")
    if state.get("current_team_id"):
        parts.append(f"Mevcut takım ID: {state['current_team_id']}")
    if state.get("user_level"):
        parts.append(f"Kullanıcı seviyesi: {state['user_level']}")
    if state.get("user_coins") is not None:
        parts.append(f"Coin: {state['user_coins']}")
    return "\n".join(parts) if parts else "Henüz kullanıcı yok."


def _extract_json(text: str) -> dict:
    """LLM çıktısından JSON bloğunu çıkarır."""
    # ```json ... ``` bloğunu ara
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())
    # Direkt JSON dene
    text = text.strip()
    if text.startswith("{"):
        return json.loads(text)
    raise ValueError(f"JSON bulunamadı: {text[:200]}")


async def router_node(state: MainState) -> dict:
    """
    Ana Router node.
    Kullanıcının son mesajını okuyup plan üretir.
    """
    messages = state.get("messages", [])
    if not messages:
        return {
            "planned_steps": [],
            "dependencies": {},
            "instructions": {},
            "global_error": "Mesaj bulunamadı.",
        }

    # Son kullanıcı mesajını al
    user_message = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            user_message = msg["content"]
            break

    recent_messages = _format_recent_messages(messages[:-1])  # Son mesaj hariç geçmiş
    context = _format_context(state)

    system_prompt = ROUTER_SYSTEM_PROMPT.format(context=context)
    user_prompt = ROUTER_USER_TEMPLATE.format(
        recent_messages=recent_messages,
        user_message=user_message,
    )

    llm = get_router_llm()
    try:
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        plan = _extract_json(response.content)
    except Exception as e:
        logger.exception("Router JSON parse hatası")
        return {
            "planned_steps": [],
            "dependencies": {},
            "instructions": {},
            "global_error": f"Planlama hatası: {str(e)}",
        }

    logger.info(f"[router] plan={plan}")

    return {
        "planned_steps": plan.get("steps", []),
        "dependencies": plan.get("dependencies", {}),
        "instructions": plan.get("instructions", {}),
        "completed_steps": [],
        "current_step": None,
        "supervisor_results": {},
        "execution_log": [],
        "global_error": None,
    }

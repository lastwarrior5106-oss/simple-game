"""
Responder Node

Hiçbir karar vermez, hiçbir araç çağırmaz.
execution_log ve state'i okuyup kullanıcıya sıcak dille yazar.
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage
from typing import AsyncGenerator

from src.services.chat_service.state.main_state import MainState
from src.services.chat_service.prompts.responder_prompt import RESPONDER_SYSTEM_PROMPT, RESPONDER_USER_TEMPLATE
from src.configs.chat import get_responder_llm

logger = logging.getLogger(__name__)

SLIDING_WINDOW = 5


def _format_recent_messages(messages: list[dict]) -> str:
    recent = messages[-SLIDING_WINDOW:] if len(messages) > SLIDING_WINDOW else messages
    lines = []
    for msg in recent:
        role = "Kullanıcı" if msg["role"] == "user" else "Asistan"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines) if lines else "(Konuşma yok)"


def _format_execution_log(execution_log: list[dict]) -> str:
    if not execution_log:
        return "Hiçbir işlem gerçekleştirilmedi."
    lines = []
    for entry in execution_log:
        icon = "✓" if entry["success"] else "✗"
        lines.append(f"{icon} {entry['supervisor']}: {entry['summary']}")
    return "\n".join(lines)


def _format_context(state: MainState) -> str:
    parts = []
    if state.get("current_user_id"):
        parts.append(f"Kullanıcı ID: {state['current_user_id']}")
    if state.get("user_level"):
        parts.append(f"Seviye: {state['user_level']}")
    if state.get("user_coins") is not None:
        parts.append(f"Coin: {state['user_coins']}")
    if state.get("current_team_id"):
        parts.append(f"Takım ID: {state['current_team_id']}")
    if state.get("global_error"):
        parts.append(f"Kritik hata: {state['global_error']}")
    return "\n".join(parts) if parts else "Bilgi yok."


def _build_prompts(state: MainState) -> tuple[str, str]:
    """System ve user prompt'larını hazırlar."""
    messages = state.get("messages", [])

    user_message = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            user_message = msg["content"]
            break

    history = [m for m in messages if not (m["role"] == "user" and m["content"] == user_message)]
    recent_messages = _format_recent_messages(history)

    execution_log_str = _format_execution_log(state.get("execution_log", []))
    context_str = _format_context(state)

    system_prompt = RESPONDER_SYSTEM_PROMPT.format(
        context=context_str,
        execution_log=execution_log_str,
    )
    user_prompt = RESPONDER_USER_TEMPLATE.format(
        recent_messages=recent_messages,
        user_message=user_message,
    )
    return system_prompt, user_prompt


async def responder_node(state: MainState) -> dict:
    """
    Responder node: execution_log'u okur, kullanıcıya yazar.
    Streaming için final_response'u tam olarak döndürür.
    """
    messages = state.get("messages", [])
    system_prompt, user_prompt = _build_prompts(state)

    llm = get_responder_llm()
    final_response = ""

    try:
        # astream ile token token üret, hepsini birleştir
        async for chunk in llm.astream([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]):
            final_response += chunk.content
    except Exception:
        logger.exception("Responder LLM hatası")
        final_response = (
            "İşlemler tamamlandı ancak yanıt oluşturulurken bir sorun yaşandı. "
            "Lütfen tekrar deneyin."
        )

    logger.info(f"[responder] yanıt uzunluğu={len(final_response)}")

    updated_messages = messages + [{"role": "assistant", "content": final_response}]

    return {
        "messages": updated_messages,
        "final_response": final_response,
    }


async def stream_responder_tokens(state: MainState) -> AsyncGenerator[str, None]:
    """
    SSE endpoint'i için: responder'ın LLM token'larını yield eder.
    Bu fonksiyon graph dışında, doğrudan SSE stream içinde çağrılır.
    """
    system_prompt, user_prompt = _build_prompts(state)
    llm = get_responder_llm()

    try:
        async for chunk in llm.astream([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]):
            if chunk.content:
                yield chunk.content
    except Exception:
        logger.exception("Responder stream hatası")
        yield "Yanıt oluşturulurken bir hata oluştu."
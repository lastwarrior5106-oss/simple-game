"""
Subgraph'lar için ortak yardımcı fonksiyonlar.

Her supervisor subgraph'ı aynı döngüyü izler:
  1. LLM'den tool çağrısı al
  2. Tool'u çalıştır
  3. Sonucu değerlendir
  4. Hata varsa retry (max 3)
  5. Bitince result paketi hazırla
"""

import json
import logging
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MAX_RETRY = 3
MAX_ITERATIONS = 10  # Sonsuz döngü önlemi


def build_tool_map(tools: list[StructuredTool]) -> dict[str, StructuredTool]:
    """Tool listesini isim bazlı dict'e çevirir."""
    return {t.name: t for t in tools}


async def run_tool_call(tool_call: dict, tool_map: dict[str, StructuredTool]) -> dict:
    """
    LLM'in ürettiği tool_call'ı çalıştırır.
    tool_call formatı: {"id": "...", "name": "...", "args": {...}}
    """
    tool_name = tool_call["name"]
    tool_args = tool_call.get("args", {})

    if tool_name not in tool_map:
        return {
            "success": False,
            "error": f"Bilinmeyen araç: {tool_name}",
        }

    tool = tool_map[tool_name]
    try:
        result = await tool.ainvoke(tool_args)
        # Tool dict döndürüyorsa direkt kullan
        if isinstance(result, dict):
            return result
        # String döndürdüyse parse et
        if isinstance(result, str):
            try:
                return json.loads(result)
            except Exception:
                return {"success": True, "output": result}
        return {"success": True, "output": result}
    except Exception as e:
        logger.exception(f"Tool çalıştırma hatası: {tool_name}")
        return {"success": False, "error": str(e)}


async def run_agent_loop(
    llm_with_tools: Any,
    system_message: str,
    initial_human_message: str,
    tools: list[StructuredTool],
) -> tuple[bool, dict, str, int]:
    """
    ReAct döngüsü: LLM → tool call → sonuç → LLM → ...

    Returns:
        (success, output, error_message, retry_count)
    """
    tool_map = build_tool_map(tools)
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=initial_human_message),
    ]

    retry_count = 0
    last_output = {}
    last_error = ""
    iteration = 0

    while iteration < MAX_ITERATIONS:
        iteration += 1
        logger.debug(f"[base] iteration={iteration}, messages_count={len(messages)}")
        try:
            response: AIMessage = await llm_with_tools.ainvoke(messages)
        except Exception as e:
            last_error = f"LLM çağrısı başarısız: {str(e)}"
            retry_count += 1
            if retry_count >= MAX_RETRY:
                return False, {}, last_error, retry_count
            continue

        messages.append(response)
        logger.debug(f"[base] tool_calls={[tc['name'] for tc in response.tool_calls]}")

        # Tool çağrısı yoksa LLM işi bitirdi
        if not response.tool_calls:
            # if not last_output:
            #     return False, {}, "LLM tool çağrısı yapmadan sonlandı.", retry_count
            return True, last_output, "", retry_count

        # Tool çağrılarını sırayla işle
        all_success = True
        for tool_call in response.tool_calls:
            result = await run_tool_call(tool_call, tool_map)
            logger.debug(f"[base] tool result={result}")
            # Tool sonucunu mesaj olarak ekle
            tool_message = ToolMessage(
                content=json.dumps(result, ensure_ascii=False),
                tool_call_id=tool_call["id"],
                name=tool_call["name"],
            )
            messages.append(tool_message)

            if result.get("success") is False:
                last_error = result.get("error", "Bilinmeyen hata")
                all_success = False
                retry_count += 1
                logger.warning(f"Tool hatası ({tool_call['name']}): {last_error} [retry: {retry_count}]")

                if retry_count >= MAX_RETRY:
                    return False, {}, last_error, retry_count
            else:
                # Başarılı sonucu biriktir
                last_output.update(result)

        # Tüm tool'lar başarısızsa LLM'e tekrar dene mesajı gönder
        if not all_success and retry_count < MAX_RETRY:
            messages.append(
                HumanMessage(content=f"Hata oluştu: {last_error}. Lütfen tekrar dene.")
            )

        

    # MAX_ITERATIONS aşıldı
    return False, last_output, "Maksimum iterasyon sayısına ulaşıldı.", retry_count

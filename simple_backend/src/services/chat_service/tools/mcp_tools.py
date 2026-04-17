import asyncio
import logging
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, create_model

from .tool_registry import AGENT_TOOLS

logger = logging.getLogger(__name__)

MCP_URL = "http://localhost:8000/mcp/sse"

MCP_CONFIG = {
    "flio": {
        "url": MCP_URL,
        "transport": "sse",
    }
}

# ── Param Injection Map ────────────────────────────────────────────────────────
# Format: { tool_name: { tool_param: context_key } }
# Buradaki parametreler LLM'e gösterilmez, state'ten otomatik inject edilir.
# "context_key" → get_tools_for_supervisor'a geçilen context dict'indeki key.
#
# actor_id   → işlemi yapan kullanıcının ID'si  (her zaman inject)
# actor_role → işlemi yapan kullanıcının rolü    (her zaman inject)
#
# target_user_id gibi "nesne" parametreleri burada YOK — LLM onları seçer.

TOOL_PARAM_MAP: dict[str, dict[str, str]] = {
    "create_team":    {"actor_id": "current_user_id", "actor_role": "current_user_role"},
    "join_team":      {"actor_id": "current_user_id", "actor_role": "current_user_role"},
    "leave_team":     {"actor_id": "current_user_id", "actor_role": "current_user_role"},
    "delete_team":    {"actor_id": "current_user_id", "actor_role": "current_user_role"},
    "level_up":       {"actor_id": "current_user_id", "actor_role": "current_user_role"},
    "delete_user":    {"actor_id": "current_user_id", "actor_role": "current_user_role"},
    "get_all_users":  {"actor_id": "current_user_id", "actor_role": "current_user_role"},
    "update_coins":   {"actor_id": "current_user_id", "actor_role": "current_user_role"},
}

# ── Wrap Helpers ───────────────────────────────────────────────────────────────

def _build_reduced_schema(tool: BaseTool, injected_params: set[str]) -> type[BaseModel]:
    original_schema = tool.args_schema
    if original_schema is None:
        return None

    # Pydantic model mi yoksa dict mi kontrol et
    if isinstance(original_schema, dict):
        # JSON Schema dict formatında geliyor
        properties = original_schema.get("properties", {})
        required = original_schema.get("required", [])
        
        fields = {}
        for field_name, field_info in properties.items():
            if field_name in injected_params:
                continue
            # JSON Schema type'ını Python type'ına çevir
            json_type = field_info.get("type", "string")
            type_map = {"string": str, "integer": int, "number": float, "boolean": bool}
            py_type = type_map.get(json_type, Any)
            
            if field_name in required:
                fields[field_name] = (py_type, ...)
            else:
                fields[field_name] = (py_type, None)
        
        if not fields:
            return create_model(f"{tool.name}_schema")
        return create_model(f"{tool.name}_schema", **fields)
    
    # Pydantic BaseModel ise orijinal mantık
    fields = {}
    for field_name, field_info in original_schema.model_fields.items():
        if field_name in injected_params:
            continue
        fields[field_name] = (field_info.annotation, field_info)

    if not fields:
        return create_model(f"{tool.name}_schema")
    return create_model(f"{tool.name}_schema", **fields)


def _wrap_tool_with_context(tool: BaseTool, injected: dict[str, Any]) -> BaseTool:
    """
    Tool'u verilen context değerleriyle sarar.
    - injected: { tool_param_adı: gerçek_değer }
    - LLM'e sunulan schema'dan inject edilen parametreler çıkarılır.
    - Çalışma zamanında LLM argümanlarına inject değerler eklenir.
    """
    reduced_schema = _build_reduced_schema(tool, set(injected.keys()))

    async def _wrapped_coroutine(**llm_kwargs) -> Any:
        merged = {**llm_kwargs, **injected}  # inject her zaman override eder
        logger.debug(f"[mcp_tools] {tool.name} çağrılıyor — merged_args={merged}")
        return await tool.ainvoke(merged)

    return StructuredTool(
        name=tool.name,
        description=tool.description,
        coroutine=_wrapped_coroutine,
        args_schema=reduced_schema,
    )


# ── Public API ─────────────────────────────────────────────────────────────────

async def get_tools_for_supervisor(
    tool_name: str,
    context: dict[str, Any] | None = None,
) -> list[BaseTool]:
    """
    Supervisor için izin verilen tool'ları döndürür.

    context örneği:
        {
            "current_user_id":   5,
            "current_user_role": "USER",   # veya "ADMIN"
            "current_team_id":   12,       # opsiyonel
        }

    TOOL_PARAM_MAP'e göre actor_id ve actor_role her zaman inject edilir;
    bu parametreler LLM'e gösterilmez ve LLM tarafından doldurulamaz.

    target_user_id gibi "nesne" parametreleri inject edilmez — LLM seçer.
    """
    allowed = AGENT_TOOLS.get(tool_name, [])
    if not allowed:
        return []

    client = MultiServerMCPClient(MCP_CONFIG)
    all_tools = await client.get_tools()
    filtered = [t for t in all_tools if t.name in allowed]

    if not context:
        return filtered

    result = []
    for tool in filtered:
        param_map = TOOL_PARAM_MAP.get(tool.name, {})
        if not param_map:
            result.append(tool)
            continue

        injected = {
            param: context[state_key]
            for param, state_key in param_map.items()
            if state_key in context and context[state_key] is not None
        }

        if not injected:
            logger.debug(f"[mcp_tools] {tool.name}: inject edilecek değer bulunamadı, orijinal kullanılıyor")
            result.append(tool)
        else:
            logger.debug(f"[mcp_tools] {tool.name}: inject={injected}")
            result.append(_wrap_tool_with_context(tool, injected))

    return result


async def get_all_tools() -> list[BaseTool]:
    client = MultiServerMCPClient(MCP_CONFIG)
    return await client.get_tools()
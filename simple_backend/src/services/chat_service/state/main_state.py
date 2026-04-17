from typing import Any, Optional
from typing_extensions import TypedDict


class SupervisorResult(TypedDict):
    """Her supervisor'ın ana graph'a döndürdüğü sonuç paketi."""
    success: bool
    output: Optional[dict]
    error: Optional[str]
    retried: int


class ExecutionLogEntry(TypedDict):
    """execution_log içindeki her kayıt."""
    supervisor: str
    success: bool
    summary: str
    output: Optional[dict]


class MainState(TypedDict):
    # ── Konuşma ──────────────────────────────────────────────────────
    messages: list[dict]          # Kullanıcı + Responder mesajları (temiz)
    router_context: list[dict]    # Son N mesaj (sliding window, Router için)

    # ── Planlama ─────────────────────────────────────────────────────
    planned_steps: list[str]      # Çalışacak supervisor adları (sıralı)
    completed_steps: list[str]    # Tamamlanan supervisor adları
    current_step: Optional[str]   # Şu an çalışan supervisor

    # ── Bağımlılık haritası ──────────────────────────────────────────
    # {"teams_supervisor": ["users_supervisor"]}
    dependencies: dict[str, list[str]]

    # ── Supervisor talimatları ───────────────────────────────────────
    # {"users_supervisor": "Kullanıcı oluştur", "teams_supervisor": "..."}
    instructions: dict[str, str]

    # ── Sonuçlar ─────────────────────────────────────────────────────
    supervisor_results: dict[str, SupervisorResult]
    execution_log: list[ExecutionLogEntry]

    # ── Aktif context ────────────────────────────────────────────────
    current_user_id: Optional[int]
    current_user_role: Optional[str]
    current_team_id: Optional[int]
    user_coins: Optional[int]
    user_level: Optional[int]

    # ── Hata ─────────────────────────────────────────────────────────
    global_error: Optional[str]

    # ── Responder çıktısı ────────────────────────────────────────────
    final_response: Optional[str]

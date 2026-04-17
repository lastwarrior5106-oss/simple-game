from dataclasses import dataclass
from src.constants import UserConstant


@dataclass
class ActionContext:
    """
    İşlemi yapan kişinin kimlik kartı.
    Servis katmanına HTTP'den de AI/MCP'den de aynı nesne geçer.
    Controller veya graph tarafından oluşturulur, LLM'e asla gösterilmez.
    """
    actor_id: int
    actor_role: str
    actor_team_id: int | None = None

    def is_admin(self) -> bool:
        return self.actor_role == UserConstant.Role.ADMIN.value

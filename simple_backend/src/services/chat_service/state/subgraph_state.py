from typing import Any, Optional
from typing_extensions import TypedDict


class SubgraphResult(TypedDict):
    """Subgraph'ın ana graph'a teslim ettiği paket."""
    success: bool
    output: Optional[dict]
    error: Optional[str]
    retried: int


class UsersState(TypedDict):
    """Users supervisor subgraph'ının kendi state'i."""
    instruction: str
    current_user_id: Optional[int]
    current_user_role: Optional[str]
    steps_done: list[str]
    retry_count: int
    last_error: Optional[str]
    result: Optional[SubgraphResult]
    internal_messages: list[dict]


class TeamsState(TypedDict):
    """Teams supervisor subgraph'ının kendi state'i."""
    instruction: str
    current_user_id: Optional[int]
    current_user_role: Optional[str]
    current_team_id: Optional[int]
    steps_done: list[str]
    retry_count: int
    last_error: Optional[str]
    result: Optional[SubgraphResult]
    internal_messages: list[dict]

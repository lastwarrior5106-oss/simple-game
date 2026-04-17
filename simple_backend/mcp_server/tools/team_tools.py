from mcp.server.fastmcp import FastMCP

from src.database.session import async_session
from src.services.team_service import TeamService
from src.models.action_context import ActionContext
from src.errors import NotFoundError, BadRequestError, AuthorizationError


def register_team_tools(mcp: FastMCP) -> None:
    """Registers all team-related tools to the MCP server."""

    @mcp.tool(
        name="create_team",
        description=(
            "Creates a new team. The creator must have sufficient coins and must not "
            "already be in a team. The team name must be unique. "
            "The creator is always the calling user; this cannot be overridden."
        ),
    )
    async def create_team(name: str, actor_id: int, actor_role: str) -> dict:
        async with async_session() as session:
            try:
                context = ActionContext(actor_id=actor_id, actor_role=actor_role)
                team, user = await TeamService.create_team(name, context, session)
                return {
                    "success": True,
                    "team_id": team.id,
                    "team_name": team.name,
                    "member_count": team.member_count,
                    "creator_remaining_coins": user.coins,
                }
            except (NotFoundError, BadRequestError, AuthorizationError) as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @mcp.tool(
        name="join_team",
        description=(
            "Adds a user to the given team. "
            "Admin can add any user; a normal user can only add themselves. "
            "Returns an error if the team is full or the user is already in a team."
        ),
    )
    async def join_team(
        target_user_id: int, team_id: int, actor_id: int, actor_role: str
    ) -> dict:
        async with async_session() as session:
            try:
                context = ActionContext(actor_id=actor_id, actor_role=actor_role)
                user, team = await TeamService.join_team(target_user_id, team_id, context, session)
                return {
                    "success": True,
                    "user_id": user.id,
                    "team_id": team.id,
                    "team_name": team.name,
                    "member_count": team.member_count,
                }
            except (NotFoundError, BadRequestError, AuthorizationError) as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @mcp.tool(
        name="leave_team",
        description=(
            "Removes a user from their current team. "
            "Admin can remove any user; a normal user can only remove themselves. "
            "Returns an error if the user is not in any team."
        ),
    )
    async def leave_team(
        target_user_id: int, actor_id: int, actor_role: str
    ) -> dict:
        async with async_session() as session:
            try:
                context = ActionContext(actor_id=actor_id, actor_role=actor_role)
                user = await TeamService.leave_team(target_user_id, context, session)
                return {
                    "success": True,
                    "user_id": user.id,
                    "team_id": None,
                }
            except (NotFoundError, BadRequestError, AuthorizationError) as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @mcp.tool(
        name="get_suggested_teams",
        description=(
            "Returns up to 10 randomly selected teams that still have open slots. "
            "Used to present team suggestions to a user."
        ),
    )
    async def get_suggested_teams() -> dict:
        async with async_session() as session:
            try:
                teams = await TeamService.get_suggested_teams(session)
                return {
                    "success": True,
                    "teams": [
                        {
                            "team_id": t.id,
                            "name": t.name,
                            "member_count": t.member_count,
                        }
                        for t in teams
                    ],
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    @mcp.tool(
        name="delete_team",
        description=(
            "Deletes the specified team and removes all its members. "
            "Admin can delete any team; a normal user can only delete their own team."
        ),
    )
    async def delete_team(
        team_id: int, actor_id: int, actor_role: str
    ) -> dict:
        async with async_session() as session:
            try:
                context = ActionContext(actor_id=actor_id, actor_role=actor_role)
                await TeamService.delete_team(team_id, context, session)
                return {"success": True, "deleted_team_id": team_id}
            except (NotFoundError, AuthorizationError) as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}
from mcp.server.fastmcp import FastMCP

from src.database.session import async_session
from src.services.user_service import UserService
from src.models.action_context import ActionContext
from src.errors import NotFoundError, AuthorizationError


def register_user_tools(mcp: FastMCP) -> None:
    """Registers all user-related tools to the MCP server."""

    @mcp.tool(
        name="level_up",
        description=(
            "Increments the specified user's level by 1 and awards them coins. "
            "Admin can level up any user; a normal user can only level up themselves. "
            "Returns an error if the user is not found."
        ),
    )
    async def level_up(target_user_id: int, actor_id: int, actor_role: str) -> dict:
        async with async_session() as session:
            try:
                context = ActionContext(actor_id=actor_id, actor_role=actor_role)
                user = await UserService.level_up(target_user_id, context, session)
                return {
                    "success": True,
                    "user_id": user.id,
                    "new_level": user.level,
                    "coins": user.coins,
                }
            except AuthorizationError as e:
                return {"success": False, "error": str(e)}
            except NotFoundError:
                return {"success": False, "error": f"User not found: {target_user_id}"}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @mcp.tool(
        name="delete_user",
        description=(
            "Deletes a user by ID. "
            "Admin can delete any user; a normal user can only delete themselves."
        ),
    )
    async def delete_user(target_user_id: int, actor_id: int, actor_role: str) -> dict:
        async with async_session() as session:
            try:
                context = ActionContext(actor_id=actor_id, actor_role=actor_role)
                await UserService.delete_user(target_user_id, context, session)
                return {"success": True, "deleted_user_id": target_user_id}
            except AuthorizationError as e:
                return {"success": False, "error": str(e)}
            except NotFoundError:
                return {"success": False, "error": f"User not found: {target_user_id}"}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @mcp.tool(
        name="get_all_users",
        description=(
            "Returns a list of all users in the system. "
            "Only admin users can call this tool."
        ),
    )
    async def get_all_users(actor_id: int, actor_role: str) -> dict:
        async with async_session() as session:
            try:
                context = ActionContext(actor_id=actor_id, actor_role=actor_role)
                users = await UserService.get_all_users(context, session)
                return {
                    "success": True,
                    "users": [
                        {
                            "user_id": u.id,
                            "email": u.email,
                            "role": u.role,
                            "level": u.level,
                            "coins": u.coins,
                            "team_id": u.team_id,
                        }
                        for u in users
                    ],
                }
            except AuthorizationError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @mcp.tool(
        name="update_coins",
        description=(
            "Sets the coin balance of the specified user to the given amount. "
            "Only admin users can call this tool."
        ),
    )
    async def update_coins(
        target_user_id: int, coins: int, actor_id: int, actor_role: str
    ) -> dict:
        async with async_session() as session:
            try:
                context = ActionContext(actor_id=actor_id, actor_role=actor_role)
                user = await UserService.update_coins(target_user_id, coins, context, session)
                return {
                    "success": True,
                    "user_id": user.id,
                    "coins": user.coins,
                }
            except AuthorizationError as e:
                return {"success": False, "error": str(e)}
            except NotFoundError:
                return {"success": False, "error": f"User not found: {target_user_id}"}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @mcp.tool(
        name="create_user",
        description=(
            "Creates a new user with the given credentials and initial stats. "
            "Email must be unique. Role must be a valid role constant. "
            "Only admin users can call this tool."
        ),
    )
    async def create_user(
        email: str, password: str, role: str, level: int, coins: int, actor_id: int, actor_role: str,
    ) -> dict:
        async with async_session() as session:
            try:
                context = ActionContext(actor_id=actor_id, actor_role=actor_role)
                
                user = await UserService.create_user(email, password, role, level, coins, context, session)
                return {
                    "success": True,
                    "user_id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "level": user.level,
                    "coins": user.coins,
                }
            except AuthorizationError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}
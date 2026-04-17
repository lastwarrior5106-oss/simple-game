from .router import Router
from src.controllers import AuthController, UserController, TeamController, AIController

auth_route = Router(router=AuthController.router, prefix='/auth')
user_route = Router(router=UserController.router, prefix='/user')
team_route = Router(router=TeamController.router, prefix='/team')
ai_route = Router(router=AIController.router, prefix="/ai")

__all__ = [
    "auth_route",
    "user_route",
    "team_route",
]
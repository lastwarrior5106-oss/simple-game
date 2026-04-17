from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models import User
from src.models.action_context import ActionContext
from src.services import UserService
from src.schemas import UserResponse, LevelUpResponse, UpdateCoinsRequest, CreateUserRequest
from src.errors import AuthorizationError
from src.utils.security import SecurityUtils
from src.constants import UserConstant

router = APIRouter(tags=["user"], include_in_schema=True)


def _make_context(user: User) -> ActionContext:
    return ActionContext(
        actor_id=user.id,
        actor_role=user.role,
        actor_team_id=user.team_id,
    )


class UserController:
    router = router

    @staticmethod
    @router.post("/", response_model=UserResponse)
    async def create_user(
        body: CreateUserRequest,
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> UserResponse:
        user = await UserService.create_user(
            email=body.email,
            password=body.password,
            role=body.role,
            level=body.level,
            coins=body.coins,
            context=_make_context(current_user), # Yeni eklenen satır
            session=session,
        )
        return UserResponse.model_validate(user)

    @staticmethod
    @router.put("/{user_id}/level-up", response_model=LevelUpResponse)
    async def level_up(
        user_id: int,
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> LevelUpResponse:
        user = await UserService.level_up(user_id, _make_context(current_user), session)
        return LevelUpResponse(id=user.id, new_level=user.level, new_coins=user.coins)

    @staticmethod
    @router.delete("/me")
    async def delete_me(
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> dict:
        await UserService.delete_user(current_user.id, _make_context(current_user), session)
        return {"message": "User deleted successfully"}

    @staticmethod
    @router.delete("/{user_id}")
    async def delete_user_by_id(
        user_id: int,
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> dict:
        await UserService.delete_user(user_id, _make_context(current_user), session)
        return {"message": "User deleted successfully"}

    @staticmethod
    @router.get("/me", response_model=UserResponse)
    async def get_me(
        current_user: User = Depends(SecurityUtils.get_current_user),
    ) -> UserResponse:
        return UserResponse.model_validate(current_user)

    @staticmethod
    @router.get("/", response_model=list[UserResponse])
    async def get_users(
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> list[User]:
        return await UserService.get_all_users(_make_context(current_user), session)

    @staticmethod
    @router.patch("/{user_id}/coins", response_model=UserResponse)
    async def update_coins(
        user_id: int,
        update_request: UpdateCoinsRequest,
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        return await UserService.update_coins(
            user_id, update_request.coins, _make_context(current_user), session
        )
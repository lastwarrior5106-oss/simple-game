from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models import User
from src.models.action_context import ActionContext
from src.services import TeamService
from src.utils.security import SecurityUtils
from src.schemas import (
    TeamResponse,
    CreateTeamResponse,
    JoinTeamResponse,
    UserResponse,
    CreateTeamRequest,
)

router = APIRouter(tags=["team"], include_in_schema=True)


def _make_context(user: User) -> ActionContext:
    return ActionContext(
        actor_id=user.id,
        actor_role=user.role,
        actor_team_id=user.team_id,
    )


class TeamController:
    router = router

    @staticmethod
    @router.post("/", response_model=CreateTeamResponse)
    async def create_team(
        payload: CreateTeamRequest,
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> CreateTeamResponse:
        team, user = await TeamService.create_team(
            payload.name, _make_context(current_user), session
        )
        return CreateTeamResponse(
            status="Team created successfully",
            team_details=TeamResponse.model_validate(team),
            creator_remaining_coins=user.coins,
        )

    @staticmethod
    @router.post("/{team_id}/join", response_model=JoinTeamResponse)
    async def join_team(
        team_id: int,
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> JoinTeamResponse:
        _, team = await TeamService.join_team(
            current_user.id, team_id, _make_context(current_user), session
        )
        return JoinTeamResponse(message="Joined team successfully", current_members=team.member_count)

    @staticmethod
    @router.post("/leave", response_model=UserResponse)
    async def leave_team(
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> UserResponse:
        """Kullanıcı kendi takımından ayrılır."""
        user = await TeamService.leave_team(
            current_user.id, _make_context(current_user), session
        )
        return UserResponse.model_validate(user)

    @staticmethod
    @router.post("/{team_id}/leave/{target_user_id}", response_model=UserResponse)
    async def leave_team_by_id(
        team_id: int,
        target_user_id: int,
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> UserResponse:
        """
        Admin başka bir kullanıcıyı takımdan çıkarır.
        Normal kullanıcı bu endpoint'e erişirse servis AuthorizationError fırlatır.
        """
        user = await TeamService.leave_team(
            target_user_id, _make_context(current_user), session
        )
        return UserResponse.model_validate(user)

    @staticmethod
    @router.get("/suggested", response_model=list[TeamResponse])
    async def get_suggested_teams(
        session: AsyncSession = Depends(get_session),
    ) -> list[TeamResponse]:
        teams = await TeamService.get_suggested_teams(session)
        return [TeamResponse.model_validate(team) for team in teams]

    @staticmethod
    @router.delete("/{team_id}")
    async def delete_team(
        team_id: int,
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> dict:
        await TeamService.delete_team(team_id, _make_context(current_user), session)
        return {"message": "Team deleted successfully"}
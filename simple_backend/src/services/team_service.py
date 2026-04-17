import random

from sqlmodel import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.configs import BusinessLogicConfig
from src.models.team import Team
from src.models.user import User
from src.models.action_context import ActionContext
from src.errors import NotFoundError, BadRequestError, AuthorizationError
from src.constants import UserConstant


class TeamService:

    @staticmethod
    async def create_team(
        name: str,
        context: ActionContext,
        session: AsyncSession,
    ):
        """
        Yetki kuralı: Herkes kendi adına takım kurabilir.
        creator her zaman context.actor_id'dir; LLM bunu seçemez.
        """
        user = await session.get(User, context.actor_id)
        if not user:
            raise NotFoundError("User not found")
        if user.coins < BusinessLogicConfig.TEAM_CREATION_COST:
            raise BadRequestError("Insufficient coins")
        if user.team_id:
            raise BadRequestError("User already in a team")

        existing = await session.execute(select(Team).where(Team.name == name))
        if existing.scalar_one_or_none():
            raise BadRequestError("Team name already taken")

        team = Team(name=name, member_count=1, owner_id=context.actor_id)
        session.add(team)
        await session.flush()

        user.coins -= BusinessLogicConfig.TEAM_CREATION_COST
        user.team_id = team.id

        await session.commit()
        await session.refresh(team)
        await session.refresh(user)
        return team, user

    @staticmethod
    async def join_team(
        target_user_id: int,
        team_id: int,
        context: ActionContext,
        session: AsyncSession,
    ):
        """
        Yetki kuralı:
          - Admin → herhangi bir kullanıcıyı takıma ekleyebilir.
          - Normal kullanıcı → yalnızca kendini ekleyebilir.
        """
        if not context.is_admin() and context.actor_id != target_user_id:
            raise AuthorizationError("You are not allowed to add other users to a team")

        user = await session.get(User, target_user_id)
        if not user:
            raise NotFoundError("User not found")
        if user.team_id:
            raise BadRequestError("User already in a team")

        result = await session.execute(
            update(Team)
            .where(
                Team.id == team_id,
                Team.member_count < BusinessLogicConfig.TEAM_CAPACITY,
            )
            .values(member_count=Team.member_count + 1)
            .returning(Team.id, Team.name, Team.member_count)
        )
        updated = result.fetchone()

        if updated is None:
            team = await session.get(Team, team_id)
            if not team:
                raise NotFoundError("Team not found")
            raise BadRequestError("Team is full")

        user.team_id = team_id
        await session.commit()
        await session.refresh(user)

        team = await session.get(Team, team_id)
        return user, team

    @staticmethod
    async def leave_team(
        target_user_id: int,
        context: ActionContext,
        session: AsyncSession,
    ) -> User:
        """
        Yetki kuralı:
          - Admin → herhangi bir kullanıcıyı takımdan çıkarabilir.
          - Normal kullanıcı → yalnızca kendini çıkarabilir.
        """
        if not context.is_admin() and context.actor_id != target_user_id:
            raise AuthorizationError("You are not allowed to remove other users from a team")

        user = await session.get(User, target_user_id)
        if not user:
            raise NotFoundError("User not found")
        if user.team_id is None:
            raise BadRequestError("User is not in a team")

        result = await session.execute(
            update(Team)
            .where(
                Team.id == user.team_id,
                Team.member_count > 0,
            )
            .values(member_count=Team.member_count - 1)
        )

        if result.rowcount == 0:
            raise BadRequestError("Team member count is invalid")

        user.team_id = None
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_suggested_teams(session: AsyncSession) -> list[Team]:
        """Herkese açık — yetki kontrolü gerekmez."""
        result = await session.execute(
            select(Team).where(Team.member_count < BusinessLogicConfig.TEAM_CAPACITY)
        )
        available_teams = result.scalars().all()
        return random.sample(
            available_teams,
            min(len(available_teams), BusinessLogicConfig.TEAM_SUGGESTION_LIMIT),
        )

    @staticmethod
    async def delete_team(
        team_id: int,
        context: ActionContext,
        session: AsyncSession,
    ) -> None:
        """
        Yetki kuralı:
          - Admin → her takımı silebilir.
          - Normal kullanıcı → yalnızca kendi kurduğu takımı silebilir.
        """
        team = await session.get(Team, team_id)
        if not team:
            raise NotFoundError("Team not found")

        if not context.is_admin() and team.owner_id != context.actor_id:
            raise AuthorizationError("You are not allowed to delete this team")

        await session.execute(
            update(User).where(User.team_id == team_id).values(team_id=None)
        )
        await session.delete(team)
        await session.commit()
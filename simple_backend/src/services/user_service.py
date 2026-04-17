from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models import User
from src.models.action_context import ActionContext
from src.configs import BusinessLogicConfig
from src.errors import NotFoundError, AuthorizationError
from src.utils.security import SecurityUtils
from src.constants import UserConstant


class UserService:

    @staticmethod
    async def create_user(
        email: str,
        password: str,
        role: str,
        level: int,
        coins: int,
        context: ActionContext,
        session: AsyncSession,
    ) -> User:
        """Yalnızca admin kullanıcılar yeni kullanıcı oluşturabilir."""
        if not context.is_admin():
            raise AuthorizationError("You are not allowed to create users")

        user = User(
            email=email,
            hashed_password=SecurityUtils.bcrypt(password),
            role=role,
            level=level,
            coins=coins,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def level_up(
        target_user_id: int,
        context: ActionContext,
        session: AsyncSession,
    ) -> User:
        """
        Yetki kuralı:
          - Admin → herkesi level-up edebilir.
          - Normal kullanıcı → yalnızca kendini level-up edebilir.
        """
        if not context.is_admin() and context.actor_id != target_user_id:
            raise AuthorizationError("You are not allowed to level up other users")

        user = await session.get(User, target_user_id)
        if not user:
            raise NotFoundError("User not found")

        user.level += BusinessLogicConfig.LEVEL_UP_INCREMENT
        user.coins += BusinessLogicConfig.LEVEL_UP_REWARD

        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def delete_user(
        target_user_id: int,
        context: ActionContext,
        session: AsyncSession,
    ) -> None:
        """
        Yetki kuralı:
          - Admin → herkesi silebilir.
          - Normal kullanıcı → yalnızca kendini silebilir.
        """
        if not context.is_admin() and context.actor_id != target_user_id:
            raise AuthorizationError("You are not allowed to delete other users")

        user = await session.get(User, target_user_id)
        if not user:
            raise NotFoundError("User not found")

        await session.delete(user)
        await session.commit()

    @staticmethod
    async def get_all_users(
        context: ActionContext,
        session: AsyncSession,
    ) -> list[User]:
        """Yalnızca admin kullanıcılar tüm listeyi görebilir."""
        if not context.is_admin():
            raise AuthorizationError("You are not allowed to view all users")

        result = await session.execute(select(User))
        return result.scalars().all()

    @staticmethod
    async def update_coins(
        target_user_id: int,
        coins: int,
        context: ActionContext,
        session: AsyncSession,
    ) -> User:
        """Yalnızca admin kullanıcılar coin güncelleyebilir."""
        if not context.is_admin():
            raise AuthorizationError("You are not allowed to update coins")

        user = await session.get(User, target_user_id)
        if not user:
            raise NotFoundError("User not found")

        user.coins = coins
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
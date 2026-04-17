from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


class UserDatabase:

    @staticmethod
    async def create_user(
        email: str,
        hashed_password: str,
        role: str,
        session: AsyncSession
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=role
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    @staticmethod
    async def get_user_by_email(
        email: str,
        session: AsyncSession
    ) -> User | None:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(
        user_id: str,
        session: AsyncSession
    ) -> User | None:
        result = await session.execute(
            select(User).where(User.id == int(user_id))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def save(
        user: User,
        session: AsyncSession
    ) -> None:
        session.add(user)
        await session.commit()
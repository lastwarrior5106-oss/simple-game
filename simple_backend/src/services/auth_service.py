from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from fastapi import HTTPException

from src.constants import UserConstant
from src.models.user import User
from src.utils import SecurityUtils, ValidationUtils
from src.utils.error import BadRequestError, UnauthorizedError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    async def register(email: str, password: str, session: AsyncSession):
        await ValidationUtils.validate_email(email, session=session)
        ValidationUtils.validate_password(password)

        from src.database import UserDatabase

        hashed_password = pwd_context.hash(password)

        user = await UserDatabase.create_user(
            email=email,
            hashed_password=hashed_password,
            role=UserConstant.Role.USER.value,
            session=session,
        )

        return {
            "message": "User registered successfully",
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
        }

    @staticmethod
    async def login(email: str, password: str, session: AsyncSession):
        from src.database import UserDatabase

        user: User | None = await UserDatabase.get_user_by_email(
            email=email,
            session=session,
        )

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not pwd_context.verify(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        tokens = SecurityUtils.generate_token(
            user_id=str(user.id),
            role=user.role,
        )

        return {
            "message": "Login successful",
            "access_token": tokens["access"],
            "refresh_token": tokens["refresh"],
            "token_type": "bearer",
            "role": user.role,
        }

    @staticmethod
    async def change_email(
        user_id: str,
        new_email: str,
        session: AsyncSession,
    ):
        await ValidationUtils.validate_email(
            new_email,
            session=session,
            skip_user_id=user_id,
        )

        from src.database import UserDatabase

        user: User | None = await UserDatabase.get_user_by_id(
            user_id=user_id,
            session=session,
        )

        if not user:
            raise UnauthorizedError(message="User not found")

        user.email = new_email
        await UserDatabase.save(user=user, session=session)

        return {
            "message": "Email changed successfully",
            "new_email": user.email,
        }

    @staticmethod
    async def change_password(
        user_id: str,
        old_password: str,
        new_password: str,
        session: AsyncSession,
    ):
        ValidationUtils.validate_password(new_password)

        from src.database import UserDatabase

        user: User | None = await UserDatabase.get_user_by_id(
            user_id=user_id,
            session=session,
        )

        if not user:
            raise UnauthorizedError(message="User not found")

        if not pwd_context.verify(old_password, user.hashed_password):
            raise BadRequestError(message="Current password is incorrect")

        user.hashed_password = pwd_context.hash(new_password)
        await UserDatabase.save(user=user, session=session)

        return {
            "message": "Password changed successfully"
        }
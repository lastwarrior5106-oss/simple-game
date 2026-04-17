from typing import Annotated

from fastapi import APIRouter, Depends, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models.user import User
from src.services.auth_service import AuthService
from src.utils.security import SecurityUtils

router = APIRouter(tags=["auth"], include_in_schema=True)


class AuthController:
    router = router

    @staticmethod
    @router.post("/register")
    async def register(
        email: Annotated[str, Body(...)],
        password: Annotated[str, Body(...)],
        session: AsyncSession = Depends(get_session)
    ):
        return await AuthService.register(email, password, session)

    @staticmethod
    @router.post("/login")
    async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_session),
    ):
        return await AuthService.login(
            form_data.username,
            form_data.password,
            session
        )

    @staticmethod
    @router.put("/change-email")
    async def change_email_endpoint(
        new_email: Annotated[str, Body(...)],
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ):
        return await AuthService.change_email(
            current_user.id,
            new_email,
            session
        )

    @staticmethod
    @router.put("/change-password")
    async def change_password_endpoint(
        old_password: Annotated[str, Body(...)],
        new_password: Annotated[str, Body(...)],
        current_user: User = Depends(SecurityUtils.get_current_user),
        session: AsyncSession = Depends(get_session),
    ):
        return await AuthService.change_password(
            current_user.id,
            old_password,
            new_password,
            session
        )

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import hashlib
import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.configs.app import AppConfig
from src.constants import UserConstant
from src.database import UserDatabase, get_session
from src.utils.error import ForbiddenError, UnauthorizedError


pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityUtils:
    oauth2_scheme = OAuth2PasswordBearer(
        tokenUrl="auth/login",
        auto_error=False,
    )

    @staticmethod
    def bcrypt(text: str) -> str:
        return pwd_cxt.hash(text)

    @staticmethod
    def verify(hashed_password: str, plain_password: str) -> bool:
        return pwd_cxt.verify(plain_password, hashed_password)

    @staticmethod
    def id_generator() -> str:
        return uuid.uuid1().hex

    @staticmethod
    def sha256(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    @staticmethod
    def generate_token(user_id: str, role: str) -> Dict[str, str]:
        access_token_payload = {
            "sub": user_id,
            "role": role,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(
                minutes=AppConfig.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
        }

        refresh_token_payload = {
            "sub": user_id,
            "role": role,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        }

        return {
            "access": jwt.encode(
                access_token_payload,
                AppConfig.SECRET_KEY,
                algorithm=AppConfig.HASHING_ALGORITHM,
            ),
            "refresh": jwt.encode(
                refresh_token_payload,
                AppConfig.SECRET_KEY,
                algorithm=AppConfig.HASHING_ALGORITHM,
            ),
        }

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(
                token,
                AppConfig.SECRET_KEY,
                algorithms=[AppConfig.HASHING_ALGORITHM],
            )
        except JWTError as exc:
            raise UnauthorizedError(
                message="Invalid or expired token",
                caught_exception=exc,
            )

    @staticmethod
    def get_token_subject(token: str) -> str:
        payload = SecurityUtils.decode_token(token)
        subject = payload.get("sub")

        if not subject:
            raise UnauthorizedError(message="Token subject not found")

        return subject

    @staticmethod
    def get_token_role(token: str) -> str:
        payload = SecurityUtils.decode_token(token)
        role = payload.get("role")

        if not role:
            raise UnauthorizedError(message="Token role not found")

        return role

    @staticmethod
    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session),
    ):
        if not token:
            raise UnauthorizedError(message="Authorization token is missing")

        user_id = SecurityUtils.get_token_subject(token)
        user = await UserDatabase.get_user_by_id(
            user_id=user_id,
            session=session,
        )

        if not user:
            raise UnauthorizedError(message="User not found")

        return user

    @staticmethod
    def require_roles(*roles: UserConstant.Role):
        async def checker(current_user=Depends(SecurityUtils.get_current_user)):
            allowed_roles = [role.value for role in roles]

            if current_user.role not in allowed_roles:
                raise ForbiddenError(
                    message="You do not have permission to access this resource"
                )

            return current_user

        return checker
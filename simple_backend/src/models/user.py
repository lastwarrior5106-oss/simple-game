from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import BaseModel

from src.constants import UserConstant


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str | None = None
    email: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)

    role: str = Field(default=UserConstant.Role.USER.value)  # 🔥 EKLENDİ

    level: int = Field(default=1)
    coins: int = Field(default=5000)

    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

class AdminCreateUserRequest(BaseModel):
    email: str
    password: str
    role: str = UserConstant.Role.USER.value
    level: int = 1
    coins: int = 5000

class CreateUserRequest(BaseModel):
    email: str
    password: str
    role: str = "USER"
    level: int = 1
    coins: int = 5000
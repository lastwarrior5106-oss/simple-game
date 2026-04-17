from pydantic import BaseModel, Field

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    level: int
    coins: int
    team_id: int | None = None

    model_config = {"from_attributes": True}


class CreateUserRequest(BaseModel):
    email: str
    password: str
    role: str = "USER"
    level: int = 1
    coins: int = 5000


class LevelUpResponse(BaseModel):
    id: int
    new_level: int
    new_coins: int


class UpdateCoinsRequest(BaseModel):
    coins: int = Field(ge=0)
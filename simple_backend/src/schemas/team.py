from pydantic import BaseModel, Field


class TeamResponse(BaseModel):
    id: int
    name: str
    member_count: int

    model_config = {"from_attributes": True}


class CreateTeamRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class CreateTeamResponse(BaseModel):
    status: str
    team_details: TeamResponse
    creator_remaining_coins: int


class JoinTeamResponse(BaseModel):
    message: str
    current_members: int
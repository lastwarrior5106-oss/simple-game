from sqlmodel import SQLModel, Field
from typing import Optional
 
 
TEAM_CAPACITY = 20
TEAM_CREATION_COST = 1000
 
 
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    owner_id: int
    member_count: int = Field(default=0)  

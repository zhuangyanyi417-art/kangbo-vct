from pydantic import BaseModel
from typing import Optional

class TeamResponse(BaseModel):
    id: int
    name: str
    region: str
    logo_url: str
    description: str
    founded_date: Optional[str] = None
    wins: int = 0
    losses: int = 0
    total_matches: int = 0
    win_rate: float = 0.0

    class Config:
        from_attributes = True

class TeamListResponse(BaseModel):
    teams: list[TeamResponse]
    total: int

class TeamStatsResponse(BaseModel):
    team_id: int
    team_name: str
    wins: int
    losses: int
    total_matches: int
    win_rate: float

from pydantic import BaseModel
from typing import Optional

class PlayerResponse(BaseModel):
    id: int
    name: str
    real_name: str
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    role: str
    country: str
    photo_url: str
    bio: str
    birth_date: Optional[str] = None
    join_date: Optional[str] = None
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    kda: float = 0.0
    headshots: int = 0
    hs_percent: float = 0.0
    matches_played: int = 0
    wins: int = 0
    win_rate: float = 0.0

    class Config:
        from_attributes = True

class PlayerListResponse(BaseModel):
    players: list[PlayerResponse]
    total: int

class PlayerStatsResponse(BaseModel):
    player_id: int
    player_name: str
    kills: int
    deaths: int
    assists: int
    kda: float
    headshots: int
    hs_percent: float
    matches_played: int
    wins: int
    win_rate: float

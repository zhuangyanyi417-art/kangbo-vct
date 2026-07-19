from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.player import Player
from app.models.team import Team
from app.schemas.player import PlayerListResponse, PlayerResponse, PlayerStatsResponse

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("", response_model=PlayerListResponse)
async def list_players(
    role: str = "",
    region: str = "",
    db: AsyncSession = Depends(get_db)
):
    query = select(Player).options(joinedload(Player.team))
    if role:
        query = query.where(Player.role == role.capitalize())
    if region:
        team_subq = select(Team.id).where(Team.region == region.upper()).subquery()
        query = query.where(Player.team_id.in_(team_subq))
    query = query.order_by(Player.wins.desc())
    result = await db.execute(query)
    players = result.unique().scalars().all()
    return PlayerListResponse(
        players=[PlayerResponse(**p.to_dict()) for p in players],
        total=len(players),
    )


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    query = select(Player).options(joinedload(Player.team)).where(Player.id == player_id)
    result = await db.execute(query)
    player = result.unique().scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="选手不存在")
    return PlayerResponse(**player.to_dict())


@router.get("/{player_id}/stats", response_model=PlayerStatsResponse)
async def get_player_stats(player_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    query = select(Player).options(joinedload(Player.team)).where(Player.id == player_id)
    result = await db.execute(query)
    player = result.unique().scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="选手不存在")
    d = player.to_dict()
    return PlayerStatsResponse(
        player_id=d["id"],
        player_name=d["name"],
        kills=d["kills"],
        deaths=d["deaths"],
        assists=d["assists"],
        kda=d["kda"],
        headshots=d["headshots"],
        hs_percent=d["hs_percent"],
        matches_played=d["matches_played"],
        wins=d["wins"],
        win_rate=d["win_rate"],
    )

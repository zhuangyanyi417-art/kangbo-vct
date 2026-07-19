from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.team import Team
from app.models.player import Player
from app.schemas.team import TeamListResponse, TeamResponse, TeamStatsResponse

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=TeamListResponse)
async def list_teams(region: str = "", db: AsyncSession = Depends(get_db)):
    query = select(Team)
    if region:
        query = query.where(Team.region == region.upper())
    query = query.order_by(Team.wins.desc())
    result = await db.execute(query)
    teams = result.scalars().all()
    return TeamListResponse(
        teams=[TeamResponse(**t.to_dict()) for t in teams],
        total=len(teams),
    )


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(team_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="战队不存在")
    return TeamResponse(**team.to_dict())


@router.get("/{team_id}/players")
async def get_team_players(team_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.team_id == team_id))
    players = result.scalars().all()
    return {"players": [p.to_dict() for p in players], "total": len(players)}


@router.get("/{team_id}/stats", response_model=TeamStatsResponse)
async def get_team_stats(team_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="战队不存在")
    return TeamStatsResponse(
        team_id=team.id,
        team_name=team.name,
        wins=team.wins,
        losses=team.losses,
        total_matches=team.wins + team.losses,
        win_rate=round(team.wins / max(team.wins + team.losses, 1) * 100, 1),
    )

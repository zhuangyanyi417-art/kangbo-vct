from app.models.team import Team
from app.models.player import Player
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ChatService:
    def __init__(self):
        self.knowledge = {}

    async def load_knowledge(self, db: AsyncSession):
        team_result = await db.execute(select(Team))
        teams = team_result.scalars().all()
        player_result = await db.execute(select(Player))
        players = player_result.scalars().all()
        self.knowledge = {"teams": teams, "players": players}

    async def answer(self, question: str, db: AsyncSession) -> str:
        await self.load_knowledge(db)
        q = question.strip().lower()
        for team in self.knowledge["teams"]:
            if team.name.lower() in q:
                members = [p for p in self.knowledge["players"] if p.team_id == team.id]
                member_names = ", ".join([p.name for p in members[:6]])
                wr = round(team.wins / max(team.wins + team.losses, 1) * 100, 1)
                return (
                    f"关于战队 {team.name}：\n"
                    f"赛区：{team.region}\n"
                    f"胜率：{wr}% ({team.wins}胜 {team.losses}负)\n"
                    f"核心选手：{member_names}\n"
                    f"简介：{team.description or '暂无'}"
                )
        for player in self.knowledge["players"]:
            if player.name.lower() in q:
                d = player.to_dict()
                return (
                    f"关于选手 {player.name}：\n"
                    f"真实姓名：{player.real_name or '暂无'}\n"
                    f"国家：{player.country}\n"
                    f"位置：{player.role}\n"
                    f"所属战队：{d['team_name'] or '暂无'}\n"
                    f"K/D/A：{d['kills']}/{d['deaths']}/{d['assists']}\n"
                    f"KDA：{d['kda']}\n"
                    f"胜率：{d['win_rate']}%"
                )
        cn_keywords = ["战队", "选手", "比赛", "赛事", "无畏契约", "valorant"]
        if any(k in q for k in cn_keywords):
            team_list = ", ".join([t.name for t in self.knowledge["teams"][:10]])
            return (
                f"平台目前有 {len(self.knowledge['teams'])} 支战队和 "
                f"{len(self.knowledge['players'])} 位选手。\n"
                f"部分战队：{team_list}\n"
                f"请输入具体战队名或选手名查询详细信息。"
            )
        return (
            "抱歉，我目前还在学习中，暂时只能回答关于 "
            "无畏契约战队和选手的问题。\n"
            "你可以尝试问：\n"
            "- '有哪些战队'\n"
            "- '某某战队的信息'\n"
            "- '某某选手的数据'"
        )

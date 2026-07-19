import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import init_db, async_session
from app.models.team import Team
from app.models.player import Player
from datetime import date


async def seed():
    await init_db()
    async with async_session() as session:
        teams_data = [
            Team(name="EDG", region="CN", wins=120, losses=45, description="EDward Gaming - 中国无畏契约强旅"),
            Team(name="FPX", region="CN", wins=98, losses=52, description="FunPlus Phoenix - 中国战队"),
            Team(name="BLG", region="CN", wins=85, losses=48, description="Bilibili Gaming - 中国新锐战队"),
            Team(name="TE", region="CN", wins=72, losses=50, description="Trace Esports - 中国战队"),
            Team(name="DRG", region="CN", wins=65, losses=55, description="Dragon Ranger Gaming - 中国战队"),
            Team(name="Sentinels", region="NA", wins=150, losses=40, description="北美传奇战队"),
            Team(name="Cloud9", region="NA", wins=130, losses=48, description="北美豪强"),
            Team(name="Fnatic", region="EMEA", wins=140, losses=42, description="欧洲传统豪门"),
            Team(name="DRX", region="KR", wins=110, losses=45, description="韩国无畏契约强旅"),
            Team(name="Gen.G", region="KR", wins=105, losses=50, description="韩国精英战队"),
            Team(name="Paper Rex", region="APAC", wins=95, losses=55, description="亚太地区强旅"),
            Team(name="LOUD", region="SA", wins=88, losses=52, description="巴西无畏契约传奇"),
        ]
        session.add_all(teams_data)
        await session.flush()

        players_data = [
            Player(name="CHICHOO", real_name="方源昊", team_id=1, role="Controller", country="中国", kills=2500, deaths=1800, assists=1500, headshots=800, matches_played=200, wins=130),
            Player(name="ZmjjKK", real_name="郑永康", team_id=1, role="Duelist", country="中国", kills=3200, deaths=2100, assists=1200, headshots=1400, matches_played=220, wins=140),
            Player(name="nobody", real_name="王聘", team_id=1, role="Sentinel", country="中国", kills=1800, deaths=1500, assists=2000, headshots=600, matches_played=190, wins=125),
            Player(name="S1Mon", real_name="赵宇晨", team_id=1, role="Initiator", country="中国", kills=2100, deaths=1700, assists=1800, headshots=750, matches_played=180, wins=120),
            Player(name="Smoggy", real_name="韩永杰", team_id=1, role="Flex", country="中国", kills=2300, deaths=1900, assists=1600, headshots=900, matches_played=200, wins=130),
            Player(name="BerLIN", real_name="李浩南", team_id=2, role="Controller", country="中国", kills=1900, deaths=1600, assists=1700, headshots=700, matches_played=170, wins=100),
            Player(name="autumn", real_name="邓秋", team_id=2, role="Duelist", country="中国", kills=2400, deaths=2000, assists=1100, headshots=1000, matches_played=180, wins=105),
            Player(name="Yuicaw", real_name="温明威", team_id=3, role="Duelist", country="中国", kills=2200, deaths=1800, assists=1300, headshots=950, matches_played=160, wins=90),
            Player(name="tenZ", real_name="Tyson Van Ngo", team_id=6, role="Duelist", country="加拿大", kills=3500, deaths=2200, assists=1800, headshots=1600, matches_played=250, wins=170),
            Player(name="aspas", real_name="Erick Santos", team_id=12, role="Duelist", country="巴西", kills=3000, deaths=2000, assists=1500, headshots=1300, matches_played=200, wins=130),
            Player(name="Derke", real_name="Nikita Sirmitev", team_id=8, role="Duelist", country="芬兰", kills=2800, deaths=1900, assists=1600, headshots=1200, matches_played=210, wins=145),
            Player(name="MaKo", real_name="Kim Myeong-kwan", team_id=9, role="Controller", country="韩国", kills=1700, deaths=1400, assists=2000, headshots=600, matches_played=180, wins=115),
            Player(name="f0rsakeN", real_name="Jason Susanto", team_id=11, role="Flex", country="印尼", kills=2600, deaths=1900, assists=1400, headshots=1100, matches_played=190, wins=110),
            Player(name="Something", real_name="Ilya Petrov", team_id=11, role="Duelist", country="俄罗斯", kills=2900, deaths=2000, assists=1200, headshots=1250, matches_played=180, wins=115),
            Player(name="yay", real_name="Jacob Whiteaker", team_id=7, role="Duelist", country="美国", kills=3100, deaths=2100, assists=1400, headshots=1500, matches_played=220, wins=150),
            Player(name="Sacy", real_name="Gustavo Rossi", team_id=6, role="Initiator", country="巴西", kills=2000, deaths=1800, assists=2200, headshots=800, matches_played=230, wins=160),
            Player(name="Meteor", real_name="Kim Tae-o", team_id=10, role="Flex", country="韩国", kills=2400, deaths=1800, assists=1500, headshots=1000, matches_played=180, wins=110),
            Player(name="Rb", real_name="Goo Sang-min", team_id=9, role="Duelist", country="韩国", kills=2500, deaths=2000, assists=1300, headshots=1050, matches_played=170, wins=105),
        ]
        session.add_all(players_data)
        await session.commit()
        print(f"已添加 {len(teams_data)} 支战队和 {len(players_data)} 位选手")
        print("=数据初始化完成!")


if __name__ == "__main__":
    asyncio.run(seed())

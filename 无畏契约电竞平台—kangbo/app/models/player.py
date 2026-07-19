from sqlalchemy import Column, Integer, String, Date, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True, comment="选手ID/昵称")
    real_name = Column(String(100), default="", comment="真实姓名")
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, comment="所属战队ID")
    role = Column(String(30), default="", comment="位置: Duelist/Initiator/Controller/Sentinel/Flex")
    country = Column(String(50), default="", comment="国家/地区")
    photo_url = Column(String(500), default="", comment="头像URL")
    bio = Column(String(1000), default="", comment="简介")
    birth_date = Column(Date, nullable=True, comment="出生日期")
    join_date = Column(Date, nullable=True, comment="加入战队日期")
    social_links = Column(JSON, default=dict, comment="社交媒体链接")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    kills = Column(Integer, default=0, comment="总击杀")
    deaths = Column(Integer, default=0, comment="总死亡")
    assists = Column(Integer, default=0, comment="总助攻")
    headshots = Column(Integer, default=0, comment="爆头数")
    matches_played = Column(Integer, default=0, comment="出场次数")
    wins = Column(Integer, default=0, comment="胜场")

    team = relationship("Team", backref="players")

    def to_dict(self):
        kda_ratio = round((self.kills + self.assists) / max(self.deaths, 1), 2)
        hs_percent = round(self.headshots / max(self.kills, 1) * 100, 1) if self.kills > 0 else 0
        return {
            "id": self.id,
            "name": self.name,
            "real_name": self.real_name,
            "team_id": self.team_id,
            "team_name": self.team.name if self.team else None,
            "role": self.role,
            "country": self.country,
            "photo_url": self.photo_url,
            "bio": self.bio,
            "birth_date": str(self.birth_date) if self.birth_date else None,
            "join_date": str(self.join_date) if self.join_date else None,
            "kills": self.kills,
            "deaths": self.deaths,
            "assists": self.assists,
            "kda": kda_ratio,
            "headshots": self.headshots,
            "hs_percent": hs_percent,
            "matches_played": self.matches_played,
            "wins": self.wins,
            "win_rate": round(self.wins / max(self.matches_played, 1) * 100, 1),
        }

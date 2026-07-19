from sqlalchemy import Column, Integer, String, Date, JSON, DateTime, func
from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True, comment="战队名称")
    region = Column(String(20), nullable=False, comment="赛区: CN/KR/NA/EMEA/APAC/SA")
    logo_url = Column(String(500), default="", comment="队标图片URL")
    description = Column(String(1000), default="", comment="简介")
    founded_date = Column(Date, nullable=True, comment="成立日期")
    social_links = Column(JSON, default=dict, comment="社交媒体链接")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    wins = Column(Integer, default=0, comment="胜场")
    losses = Column(Integer, default=0, comment="负场")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "region": self.region,
            "logo_url": self.logo_url,
            "description": self.description,
            "founded_date": str(self.founded_date) if self.founded_date else None,
            "wins": self.wins,
            "losses": self.losses,
            "total_matches": self.wins + self.losses,
            "win_rate": round(self.wins / (self.wins + self.losses) * 100, 1) if (self.wins + self.losses) > 0 else 0,
        }

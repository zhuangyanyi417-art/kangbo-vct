from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, func
from app.database import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_a_id = Column(Integer, ForeignKey("teams.id"), nullable=False, comment="战队A ID")
    team_b_id = Column(Integer, ForeignKey("teams.id"), nullable=False, comment="战队B ID")
    event_name = Column(String(200), default="", comment="赛事名称")
    match_date = Column(DateTime, nullable=True, comment="比赛时间")
    status = Column(String(20), default="upcoming", comment="状态: upcoming/ongoing/completed")
    score_a = Column(Integer, default=0, comment="战队A得分")
    score_b = Column(Integer, default=0, comment="战队B得分")
    maps_data = Column(JSON, default=list, comment="地图详情")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "team_a_id": self.team_a_id,
            "team_b_id": self.team_b_id,
            "event_name": self.event_name,
            "match_date": self.match_date.isoformat() if self.match_date else None,
            "status": self.status,
            "score_a": self.score_a,
            "score_b": self.score_b,
            "maps_data": self.maps_data,
        }

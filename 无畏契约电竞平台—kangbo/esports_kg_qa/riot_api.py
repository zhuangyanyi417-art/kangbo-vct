"""
Riot Games Valorant API 客户端
文档: https://developer.riotgames.com/apis
"""
import httpx
import time
import json
from datetime import datetime

# Riot API 区域映射
REGIONS = {
    'NA': 'americas', 'BR': 'americas', 'LATAM': 'americas',
    'EU': 'europe', 'TR': 'europe', 'RU': 'europe',
    'KR': 'asia', 'JP': 'asia',
    'APAC': 'asia', 'SEA': 'asia',
}

MATCH_REGIONS = {
    'NA': 'na', 'BR': 'br', 'LATAM': 'latam',
    'EU': 'eu', 'TR': 'eu', 'RU': 'eu',
    'KR': 'kr', 'APAC': 'ap', 'JP': 'ap',
}


class RiotAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base = "https://{}.api.riotgames.com"
        self._last_request = 0
        self._min_interval = 0.05  # 20 req/s 上限

    def _rate_limit(self):
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def _request(self, method, url, **kwargs):
        self._rate_limit()
        headers = {"X-Riot-Token": self.api_key, **kwargs.pop("headers", {})}
        try:
            r = httpx.request(method, url, headers=headers, timeout=10, **kwargs)
            if r.status_code == 429:
                retry = int(r.headers.get("Retry-After", 1))
                print(f"  限流，等待 {retry}s...")
                time.sleep(retry)
                return self._request(method, url, **kwargs)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    # ---- 账号 API ----
    def get_puuid(self, game_name, tag_line="NA1"):
        """通过 Riot ID 获取 PUUID"""
        url = f"{self.base.format('americas')}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        data = self._request("GET", url)
        if data:
            return data.get("puuid")
        # 尝试其他常见 tagline
        for tag in ["CN1", "KR1", "EUW", "EUNE", "BR1", "LA1", "LA2", "OCE"]:
            if tag == tag_line:
                continue
            url = f"{self.base.format('americas')}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag}"
            data = self._request("GET", url)
            if data:
                return data.get("puuid")
        return None

    # ---- 比赛 API ----
    def get_recent_matches(self, puuid, region="na", count=20):
        """获取最近比赛 ID 列表"""
        url = f"{self.base.format('americas')}/val/match/v1/matches/by-puuid/{puuid}/ids"
        params = {"start": 0, "count": count}
        data = self._request("GET", url, params=params)
        return data if data else []

    def get_match_details(self, match_id):
        """获取单场比赛详情"""
        url = f"{self.base.format('americas')}/val/match/v1/matches/{match_id}"
        return self._request("GET", url)

    # ---- 数据解析 ----
    def parse_match(self, match_data):
        """将 Riot API 的比赛数据解析为 CSV 行格式"""
        if not match_data:
            return []
        
        info = match_data.get("matchInfo", {})
        players = match_data.get("players", [])
        teams = match_data.get("teams", [])
        map_id = info.get("mapId", "").split("/")[-1] or "Unknown"
        
        # 队伍分数
        team_scores = {t["teamId"]: t.get("roundsWon", 0) for t in teams}
        team_wins = {t["teamId"]: t.get("won", False) for t in teams}
        
        rows = []
        for p in players:
            stats = p.get("stats", {})
            team_id = p.get("teamId", "")
            team_name = p.get("gameName", "Unknown")
            
            kills = stats.get("kills", 0)
            deaths = stats.get("deaths", 0)
            assists = stats.get("assists", 0)
            score = stats.get("score", 0)
            
            # 计算 ACS = 总评分 / 回合数
            total_rounds = sum(team_scores.values())
            acs = round(score / max(total_rounds, 1), 1) if total_rounds > 0 else 0
            
            # 爆头率
            head = stats.get("shotsHead", 0)
            body = stats.get("shotsBody", 0)
            leg = stats.get("shotsLeg", 0)
            total_shots = head + body + leg
            hs_pct = round(head / max(total_shots, 1) * 100, 1) if total_shots > 0 else 0
            
            opponent_id = "Blue" if team_id == "Red" else "Red"
            
            rows.append({
                "match_id": info.get("matchId", ""),
                "game_id": 0,
                "team": team_name,
                "score_team": team_scores.get(team_id, 0),
                "opponent": opponent_id,
                "score_opp": team_scores.get(opponent_id, 0),
                "win_lose": "team win" if team_wins.get(team_id) else "opponent win",
                "map": map_id,
                "map_pick": "N/A",
                "player_id": 0,
                "player": team_name,
                "agent": p.get("agentId", "").split("/")[-1] if p.get("agentId") else "Unknown",
                "rating": 0,
                "acs": acs,
                "kill": kills,
                "death": deaths,
                "assist": assists,
                "kast%": 0,
                "adr": round(score / max(total_rounds, 1), 1),
                "hs%": hs_pct,
                "fk": stats.get("firstBloodsGiven", 0),
                "fd": 0,
            })
        
        return rows


if __name__ == "__main__":
    # 测试
    print("Riot API 模块加载成功")
    print("使用方法:")
    print("  api = RiotAPI('RGAPI-xxx')")
    print("  puuid = api.get_puuid('PlayerName', 'NA1')")
    print("  matches = api.get_recent_matches(puuid)")
    print("  data = api.get_match_details(matches[0])")
    print("  rows = api.parse_match(data)")

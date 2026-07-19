from neo4j import GraphDatabase


class AnswerSearcher:
    def __init__(self, uri="bolt://localhost:7687", auth=("neo4j", "dzl123456")):
        self.uri = uri
        self.auth = auth
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(self.uri, auth=self.auth)
            try:
                self._driver.verify_connectivity()
                print("数据库连接成功")
            except Exception as e:
                print(f"数据库连接失败: {e}")
                self._driver = None
        return self._driver

    def search(self, intent, slots):
        if intent is None:
            return ("抱歉，我暂时无法理解你的问题。你可以试试：\n"
                    "- DRX 有哪些选手？\n"
                    "- MaKo 是哪个战队的？\n"
                    "- zekken 的表现怎么样？\n"
                    "- FNC 属于哪个赛区？\n"
                    "- 谁是最强选手？\n"
                    "- EDG 最强的选手是谁？")

        if self._driver is None:
            return "数据库未连接，请先启动 Neo4j 服务。"

        with self.driver.session() as session:
            try:
                if intent == 'team_players':
                    query = """
                    MATCH (t:Team {name: $team})<-[:PLAYS_FOR]-(p:Player)
                    RETURN p.name AS player
                    ORDER BY p.name
                    """
                    recs = session.run(query, team=slots['team']).data()
                    if not recs:
                        return f"未找到战队 {slots['team']} 的选手信息。"
                    players = [r['player'] for r in recs]
                    return f"战队 {slots['team']} 的选手有：{', '.join(players)}"

                elif intent == 'player_team':
                    query = """
                    MATCH (p:Player {name: $player})-[:PLAYS_FOR]->(t:Team)
                    RETURN t.name AS team
                    """
                    recs = session.run(query, player=slots['player']).data()
                    if not recs:
                        return f"未找到选手 {slots['player']} 的战队信息。"
                    teams = [r['team'] for r in recs]
                    return f"选手 {slots['player']} 效力的战队有：{', '.join(teams)}"

                elif intent == 'player_performance':
                    query = """
                    MATCH (p:Player {name: $player})-[r:PLAYED_IN]->(m:Match)
                    RETURN m.match_id AS match_id,
                           r.ACS AS acs, r.Rating AS rating,
                           r.Kills AS kills, r.Deaths AS deaths, r.Assists AS assists,
                           r.ADR AS adr, r.KAST AS kast, r.Games AS games
                    ORDER BY r.ACS DESC
                    LIMIT 5
                    """
                    recs = session.run(query, player=slots['player']).data()
                    if not recs:
                        return f"未找到选手 {slots['player']} 的表现数据。"
                    lines = [f"选手 {slots['player']} 的最佳表现："]
                    for r in recs:
                        lines.append(
                            f"· 比赛 {r['match_id']}：ACS {r['acs']}，"
                            f"Rating {r['rating']}，{r['games']}张地图，"
                            f"K/D/A {r['kills']}/{r['deaths']}/{r['assists']}，"
                            f"ADR {r['adr']}"
                        )
                    return "\n".join(lines)

                elif intent == 'team_region':
                    query = """
                    MATCH (t:Team {name: $team})-[:FROM_REGION]->(r:Region)
                    RETURN r.name AS region
                    """
                    rec = session.run(query, team=slots['team']).single()
                    if rec:
                        return f"战队 {slots['team']} 属于 {rec['region']} 赛区。"
                    else:
                        return f"未找到战队 {slots['team']} 的地区信息。"

                elif intent == 'player_region':
                    query = """
                    MATCH (p:Player {name: $player})-[:PLAYS_FOR]->(t:Team)-[:FROM_REGION]->(r:Region)
                    RETURN DISTINCT r.name AS region
                    """
                    recs = session.run(query, player=slots['player']).data()
                    regions = list(set(r['region'] for r in recs))
                    if regions:
                        return f"选手 {slots['player']} 所在的赛区为：{', '.join(regions)}"
                    else:
                        return f"未找到选手 {slots['player']} 的赛区信息。"

                elif intent == 'player_events':
                    query = """
                    MATCH (p:Player {name: $player})-[r:PLAYED_IN]->(m:Match)
                    RETURN DISTINCT m.match_id AS match_id
                    ORDER BY match_id
                    """
                    recs = session.run(query, player=slots['player']).data()
                    events = [str(r['match_id']) for r in recs]
                    if events:
                        return f"选手 {slots['player']} 参加了 {len(events)} 场比赛。"
                    else:
                        return f"未找到选手 {slots['player']} 的参赛记录。"

                elif intent == 'player_best_acs':
                    query = """
                    MATCH (p:Player)-[r:PLAYED_IN]->(m:Match)
                    WHERE r.ACS IS NOT NULL
                    WITH p, r, m
                    ORDER BY r.ACS DESC
                    LIMIT 1
                    RETURN p.name AS player, r.ACS AS acs, r.Kills AS kills,
                           r.Deaths AS deaths, r.Assists AS assists
                    """
                    rec = session.run(query).single()
                    if rec:
                        return (f"所有选手中 ACS 最高的是 {rec['player']}，"
                                f"ACS: {rec['acs']}，KDA: {rec['kills']}/{rec['deaths']}/{rec['assists']}")
                    else:
                        return "未找到任何表现数据。"

                elif intent == 'team_best_player':
                    query = """
                    MATCH (t:Team {name: $team})<-[:PLAYS_FOR]-(p:Player)-[r:PLAYED_IN]->(m:Match)
                    WITH p, r, t
                    ORDER BY r.ACS DESC
                    LIMIT 1
                    RETURN p.name AS player, r.ACS AS acs,
                           r.Kills AS kills, r.Deaths AS deaths, r.Assists AS assists
                    """
                    rec = session.run(query, team=slots['team']).single()
                    if rec:
                        return (f"战队 {slots['team']} 中 ACS 最高的选手是 {rec['player']}，"
                                f"ACS: {rec['acs']}，KDA: {rec['kills']}/{rec['deaths']}/{rec['assists']}")
                    else:
                        return f"未找到战队 {slots['team']} 的选手表现数据。"

                else:
                    return "抱歉，我暂时无法回答该问题。"

            except Exception as e:
                return f"查询出错：{e}"

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

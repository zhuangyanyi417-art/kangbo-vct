from neo4j import GraphDatabase
import pandas as pd

CSV_PATH = "/Users/luka/Documents/无畏契约电竞平台—kangbo/esports_kg_qa/data/vlr_dataset.csv"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "dzl123456")

TEAM_REGION_BY_ABBREV = {
    '100T': 'NA', 'ASE': 'CN', 'BBL': 'EMEA', 'BLG': 'CN',
    'BNY': 'APAC', 'C9': 'NA', 'DFM': 'APAC', 'DRX': 'KR',
    'EDG': 'CN', 'EG': 'NA', 'FNC': 'EMEA', 'FPX': 'CN',
    'FUR': 'SA', 'FUT': 'EMEA', 'GE': 'APAC', 'GEN': 'KR',
    'GIA': 'EMEA', 'KC': 'EMEA', 'KOI': 'EMEA', 'KRU': 'SA',
    'LEV': 'SA', 'LOUD': 'SA', 'MIBR': 'SA', 'NAVI': 'EMEA',
    'NRG': 'NA', 'PRX': 'APAC', 'RRQ': 'APAC', 'SEN': 'NA',
    'SPB': 'APAC', 'T1': 'KR', 'TH': 'EMEA', 'TL': 'EMEA',
    'TLN': 'APAC', 'TS': 'APAC', 'VIT': 'EMEA', 'ZETA': 'APAC',
}
# 战队全名 → 缩写映射
TEAM_ABBREV = {
    '100 Thieves': '100T', 'All Gamers': 'AG', 'BBL Esports': 'BBL',
    'Bilibili Gaming': 'BLG', 'Cloud9': 'C9', 'Dragon Ranger Gaming': 'DRG',
    'EDward Gaming': 'EDG', 'ENVY': 'ENVY', 'Eternal Fire': 'EF',
    'Evil Geniuses': 'EG', 'FNATIC': 'FNC', 'FURIA': 'FUR',
    'FUT Esports': 'FUT', 'FunPlus Phoenix': 'FPX', 'G2 Esports': 'G2',
    'GIANTX': 'GIA', 'Gentle Mates': 'GM', 'JDG Esports': 'JDG',
    'KRÜ Esports': 'KRU', 'Karmine Corp': 'KC', 'LEVIATÁN': 'LEV',
    'LOUD': 'LOUD', 'MIBR': 'MIBR', 'NRG': 'NRG',
    'Natus Vincere': 'NAVI', 'Nova Esports': 'NOVA', 'PCIFIC Esports': 'PCIFIC',
    'Sentinels': 'SEN', 'TYLOO': 'TYL', 'Team Heretics': 'TH',
    'Team Liquid': 'TL', 'Team Vitality': 'VIT', 'Titan Esports Club': 'TEC',
    'Trace Esports': 'TE', 'Wolves Esports': 'WOL', 'Xi Lai Gaming': 'XLG',
}

# 用全名重建赛区映射
TEAM_REGION = {}
for full_name, abbr in TEAM_ABBREV.items():
    if abbr in TEAM_REGION_BY_ABBREV:
        TEAM_REGION[full_name] = TEAM_REGION_BY_ABBREV[abbr]
TEAM_REGION['Unknown'] = 'Unknown'


AGENT_ROLE = {
    'jett': 'Duelist', 'raze': 'Duelist', 'phoenix': 'Duelist', 'reyna': 'Duelist',
    'yoru': 'Duelist', 'iso': 'Duelist', 'neon': 'Duelist',
    'sova': 'Initiator', 'skye': 'Initiator', 'breach': 'Initiator',
    'kayo': 'Initiator', 'fade': 'Initiator', 'gekko': 'Initiator',
    'omen': 'Controller', 'viper': 'Controller', 'astra': 'Controller',
    'brimstone': 'Controller', 'harbor': 'Controller', 'clove': 'Controller',
    'killjoy': 'Sentinel', 'cypher': 'Sentinel', 'sage': 'Sentinel',
    'chamber': 'Sentinel', 'deadlock': 'Sentinel', 'vyse': 'Sentinel',
}


def load_and_clean():
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    num_cols = ['acs', 'rating', 'adr', 'kill', 'death', 'assist', 'kast%', 'hs%', 'fk', 'fd']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True),
                                     errors='coerce').fillna(0)
    return df


def flush_player_match_batch(session, batch):
    for item in batch:
        session.run("""
            MERGE (p:Player {name: $pname})
            MERGE (m:Match {match_id: $mid})
            MERGE (p)-[r:PLAYED_IN]->(m)
            SET r.ACS = $avg_acs, r.Rating = $avg_rating,
                r.Kills = $kills, r.Deaths = $deaths, r.Assists = $assists,
                r.KAST = $avg_kast, r.ADR = $avg_adr, r.HS = $avg_hs,
                r.FK = $fk, r.FD = $fd, r.Games = $games,
                r.Win = CASE WHEN $win_lose = 'team win' THEN true ELSE false END,
                r.Team = $team
        """, mid=item['match_id'], pname=item['player_name'],
            avg_acs=item['avg_acs'], avg_rating=item['avg_rating'],
            kills=item['kills'], deaths=item['deaths'], assists=item['assists'],
            avg_kast=item['avg_kast'], avg_adr=item['avg_adr'],
            avg_hs=item['avg_hs'], fk=item['fk'], fd=item['fd'],
            games=item['games_played'], win_lose=item['win_lose'],
            team=item['team_name'])
        session.run("""
            MATCH (p:Player {name: $pname})
            MATCH (t:Team {name: $team})
            MERGE (p)-[:PLAYS_FOR]->(t)
        """, pname=item['player_name'], team=item['team_name'])


def build_graph(driver):
    df = load_and_clean()

    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("清空数据库完成")

        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Player) REQUIRE p.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Team) REQUIRE t.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:Match) REQUIRE m.match_id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Agent) REQUIRE a.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Region) REQUIRE r.name IS UNIQUE")
        print("约束创建完成")

        # Region nodes
        for reg in set(TEAM_REGION.values()):
            session.run("MERGE (r:Region {name: $name})", name=reg)
        print(f"创建了 {len(set(TEAM_REGION.values()))} 个赛区节点")

        # Team nodes + FROM_REGION
        for team_name in df['team'].unique():
            region = TEAM_REGION.get(team_name, 'Unknown')
            session.run("""
                MERGE (t:Team {name: $name})
                MERGE (r:Region {name: $region})
                MERGE (t)-[:FROM_REGION]->(r)
            """, name=team_name, region=region)
        print(f"创建了 {df['team'].nunique()} 个战队节点")

        # Player nodes
        players = df[['player_id', 'player']].drop_duplicates()
        for _, row in players.iterrows():
            session.run("""
                MERGE (p:Player {name: $name})
                SET p.player_id = $pid
            """, name=row['player'], pid=row['player_id'])
        print(f"创建了 {len(players)} 个选手节点")

        # Player-Match PLAYED_IN + PLAYS_FOR
        match_groups = df.groupby(['match_id', 'player_id', 'player', 'team'])
        batch = []
        batch_size = 100
        total_groups = 0

        for (mid, pid, pname, team_name), group in match_groups:
            total_groups += 1
            avg_acs = round(float(group['acs'].mean()), 1)
            avg_rating = round(float(group['rating'].mean()), 2)
            avg_kast = round(float(group['kast%'].mean()), 1)
            avg_adr = round(float(group['adr'].mean()), 1)
            avg_hs = round(float(group['hs%'].mean()), 1)

            batch.append({
                'match_id': int(mid), 'player_id': int(pid),
                'player_name': pname, 'team_name': team_name,
                'kills': int(group['kill'].sum()),
                'deaths': int(group['death'].sum()),
                'assists': int(group['assist'].sum()),
                'avg_acs': avg_acs, 'avg_rating': avg_rating,
                'avg_kast': avg_kast, 'avg_adr': avg_adr,
                'avg_hs': avg_hs,
                'fk': int(group['fk'].sum()),
                'fd': int(group['fd'].sum()),
                'games_played': len(group),
                'win_lose': group['win_lose'].iloc[0],
            })

            if len(batch) >= batch_size:
                flush_player_match_batch(session, batch)
                batch = []

        if batch:
            flush_player_match_batch(session, batch)

        print(f"创建了 {total_groups} 条选手-比赛关系")

        # Match nodes + INVOLVES relationships
        match_infos = df[['match_id', 'team', 'opponent', 'map']].drop_duplicates()
        match_ids = match_infos['match_id'].unique()
        for mid in match_ids:
            mdf = match_infos[match_infos['match_id'] == mid]
            match_teams = mdf['team'].unique().tolist()
            maps_played = mdf['map'].unique().tolist()
            session.run("""
                MERGE (m:Match {match_id: $mid})
                SET m.maps = $maps, m.map_count = size($maps)
            """, mid=int(mid), maps=maps_played)
            for t in match_teams:
                session.run("""
                    MATCH (m:Match {match_id: $mid})
                    MATCH (t:Team {name: $team})
                    MERGE (m)-[:INVOLVES]->(t)
                """, mid=int(mid), team=t)

        print(f"创建了 {len(match_ids)} 个比赛节点")

        # Agent nodes
        for agent_name in df['agent'].unique():
            role = AGENT_ROLE.get(agent_name.lower(), 'Unknown')
            session.run("""
                MERGE (a:Agent {name: $name})
                SET a.role = $role
            """, name=agent_name, role=role)
        print(f"创建了 {df['agent'].nunique()} 个英雄节点")

        # Stats
        pc = session.run("MATCH (p:Player) RETURN count(p) AS c").single()['c']
        tc = session.run("MATCH (t:Team) RETURN count(t) AS c").single()['c']
        mc = session.run("MATCH (m:Match) RETURN count(m) AS c").single()['c']
        rc = session.run("MATCH ()-[r:PLAYED_IN]->() RETURN count(r) AS c").single()['c']

        print(f"\n{'='*40}")
        print(f"知识图谱构建完成！")
        print(f"  选手: {pc}")
        print(f"  战队: {tc}")
        print(f"  比赛: {mc}")
        print(f"  选手-比赛记录: {rc}")
        print(f"{'='*40}")


if __name__ == '__main__':
    print("正在连接 Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    driver.verify_connectivity()
    print("连接成功，开始构建知识图谱...")
    build_graph(driver)
    driver.close()
    print("\n全部完成！")

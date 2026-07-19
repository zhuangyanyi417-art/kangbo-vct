from flask import Flask, request, jsonify, render_template
from question_classifier import build_entity_automaton, QuestionClassifier
from answer_search import AnswerSearcher
import llm_service
import scraper
import pandas as pd
from build_kg import TEAM_REGION

# 战队缩写 → 全名映射（让用户说 "EDG" 也能识别为 "EDward Gaming"）
TEAM_ALIASES = {
    "100T": "100 Thieves", "AG": "All Gamers", "BBL": "BBL Esports",
    "BLG": "Bilibili Gaming", "C9": "Cloud9", "DRG": "Dragon Ranger Gaming",
    "EDG": "EDward Gaming", "EG": "Evil Geniuses", "FNC": "FNATIC",
    "FPX": "FunPlus Phoenix", "FUR": "FURIA", "FUT": "FUT Esports",
    "G2": "G2 Esports", "GIA": "GIANTX", "GM": "Gentle Mates",
    "JDG": "JDG Esports", "KC": "Karmine Corp", "KRU": "KRU Esports",
    "LEV": "LEVIATAN", "LOUD": "LOUD", "MIBR": "MIBR",
    "NRG": "NRG", "NAVI": "Natus Vincere", "NOVA": "Nova Esports",
    "SEN": "Sentinels", "TYL": "TYLOO", "TH": "Team Heretics",
    "TL": "Team Liquid", "VIT": "Team Vitality", "TEC": "Titan Esports Club",
    "TE": "Trace Esports", "WOL": "Wolves Esports", "XLG": "Xi Lai Gaming",
    "ENVY": "ENVY", "EF": "Eternal Fire", "PCIFIC": "PCIFIC Esports",
}

app = Flask(__name__)

CSV_PATH = "/Users/luka/Documents/无畏契约电竞平台—kangbo/esports_kg_qa/data/vlr_dataset.csv"
NEO4J_AUTH = ("neo4j", "dzl123456")

history = []

# ================== 初始化组件 ==================
print("正在加载实体自动机...")
automaton = build_entity_automaton(CSV_PATH)
classifier = QuestionClassifier(automaton)

print("正在初始化问答组件...")
searcher = AnswerSearcher(auth=NEO4J_AUTH)
print("系统就绪！")


# 修改: 去掉多余的verify_connectivity调用
import time
def get_driver():
    """延迟获取 Neo4j driver，连接失败时返回 None"""
    try:
        d = searcher.driver
        if d:
            return d
        # 首次连接失败，重试一次
        time.sleep(1)
        searcher._driver = None
        d = searcher.driver
        return d
    except Exception as e:
        print(f"Neo4j连接失败: {e}")
    return None


# ================== 页面路由 ==================
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/qa')
def qa_page():
    return render_template('qa.html')

@app.route('/players')
def player_list():
    return render_template('player_list.html')

@app.route('/rankings')
def rankings_page():
    return render_template('rankings.html')


# ================== 数据 API ==================
@app.route('/api/hot_players')
def api_hot_players():
    driver = get_driver()
    if not driver:
        return jsonify([])
    with driver.session() as session:
        query = """
        MATCH (p:Player)-[r:PLAYED_IN]->(m:Match)
        WHERE r.ACS IS NOT NULL
        WITH p, avg(r.ACS) AS avg_acs, count(m) AS match_count
        ORDER BY avg_acs DESC
        LIMIT 6
        RETURN p.name AS player, round(avg_acs, 1) AS avg_acs, match_count
        """
        return jsonify(session.run(query).data())

@app.route('/api/region_distribution')
def api_region_distribution():
    driver = get_driver()
    if not driver:
        return jsonify([])
    with driver.session() as session:
        query = """
        MATCH (r:Region)<-[:FROM_REGION]-(t:Team)
        RETURN r.name AS region, count(t) AS team_count
        ORDER BY region
        """
        return jsonify(session.run(query).data())

@app.route('/api/players', methods=['GET'])
def api_players():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    team = request.args.get('team', '').strip()
    player_name = request.args.get('player', '').strip()
    search = request.args.get('search', '').strip().lower()

    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    original_columns = df.columns.tolist()

    if team:
        df = df[df['team'].str.strip() == team]
    if player_name:
        df = df[df['player'].str.strip() == player_name]
    if search:
        mask = pd.Series(False, index=df.index)
        for col in df.select_dtypes(include='object').columns:
            mask |= df[col].astype(str).str.lower().str.contains(search, na=False)
        df = df[mask]

    df = df[original_columns]
    total = len(df)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages) if total_pages > 0 else 1
    start = (page - 1) * per_page
    end = start + per_page
    chunk = df.iloc[start:end].fillna('')
    records = chunk.to_dict(orient='records')
    return jsonify({
        'columns': original_columns,
        'data': records,
        'page': page,
        'total_pages': total_pages,
        'total': total
    })

@app.route('/api/filter_options')
def filter_options():
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    options = {
        'teams': sorted(df['team'].dropna().unique().tolist()),
        'players': sorted(df['player'].dropna().unique().tolist()),
    }
    return jsonify(options)

@app.route('/api/region_avg_acs')
def region_avg_acs():
    driver = get_driver()
    if not driver:
        return jsonify([])
    with driver.session() as session:
        query = """
        MATCH (t:Team)-[:FROM_REGION]->(r:Region)
        MATCH (p:Player)-[:PLAYS_FOR]->(t)
        MATCH (p)-[pi:PLAYED_IN]->(:Match)
        RETURN r.name AS region, round(avg(pi.ACS), 1) AS avg_acs
        ORDER BY avg_acs DESC
        """
        return jsonify(session.run(query).data())

@app.route('/api/top10_players')
def top10_players():
    driver = get_driver()
    if not driver:
        return jsonify([])
    with driver.session() as session:
        query = """
        MATCH (p:Player)-[pi:PLAYED_IN]->(:Match)
        WHERE pi.ACS IS NOT NULL
        WITH p, round(avg(pi.ACS), 1) AS avg_acs
        ORDER BY avg_acs DESC
        LIMIT 10
        RETURN p.name AS player, avg_acs
        """
        return jsonify(session.run(query).data())

@app.route('/api/region_player_count')
def region_player_count():
    driver = get_driver()
    if not driver:
        return jsonify([])
    with driver.session() as session:
        query = """
        MATCH (t:Team)-[:FROM_REGION]->(r:Region)
        MATCH (p:Player)-[:PLAYS_FOR]->(t)
        RETURN r.name AS region, count(DISTINCT p) AS player_count
        ORDER BY player_count DESC
        """
        return jsonify(session.run(query).data())

@app.route('/api/rankings')
def api_rankings():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    sort_by = request.args.get('sort_by', 'acs').strip().lower()
    region = request.args.get('region', '').strip()
    team = request.args.get('team', '').strip()

    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    num_cols = ['acs','rating','adr','kill','death','assist','kast%','hs%','fk','fd']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True),
                                     errors='coerce').fillna(0)

    grouped = df.groupby(['player', 'team']).agg(
        avg_acs=('acs', 'mean'),
        avg_rating=('rating', 'mean'),
        avg_adr=('adr', 'mean'),
        avg_kast=('kast%', 'mean'),
        avg_hs=('hs%', 'mean'),
        total_kills=('kill', 'sum'),
        total_deaths=('death', 'sum'),
        total_assists=('assist', 'sum'),
        match_count=('match_id', 'nunique'),
        game_count=('game_id', 'count')
    ).reset_index()

    # 所有指标保留两位小数
    for col in ['avg_acs', 'avg_rating', 'avg_adr', 'avg_kast', 'avg_hs']:
        grouped[col] = grouped[col].round(2)

    grouped['kda'] = round(
        (grouped['total_kills'] + grouped['total_assists']) / grouped['total_deaths'].replace(0, 1), 2
    )

    if region:
        from build_kg import TEAM_REGION
        teams_in_region = [t for t, r in TEAM_REGION.items() if r == region]
        grouped = grouped[grouped['team'].isin(teams_in_region)]
    if team:
        grouped = grouped[grouped['team'] == team]

    sort_map = {
        'acs': 'avg_acs', 'rating': 'avg_rating', 'adr': 'avg_adr',
        'kast': 'avg_kast', 'hs': 'avg_hs', 'kda': 'kda',
        'kills': 'total_kills'
    }
    sort_column = sort_map.get(sort_by, 'avg_acs')
    grouped = grouped.sort_values(sort_column, ascending=False)

    total = len(grouped)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    end = start + per_page
    chunk = grouped.iloc[start:end].fillna('')
    records = chunk.to_dict(orient='records')

    return jsonify({
        'data': records,
        'page': page,
        'total_pages': total_pages,
        'total': total
    })

# ================== 问答接口 ==================
def _retrieve_kg_context(parsed):
    """根据解析结果，从知识图谱检索上下文数据"""
    # 检查数据库连接
    if searcher._driver is None:
        return None
    context = []
    intent = parsed.get('intent')
    slots = parsed.get('slots', {})

    if intent == 'team_players' and 'team' in slots:
        team = slots['team']
        region = TEAM_REGION.get(team, 'Unknown')
        context.append(f'战队 {team} 属于 {region} 赛区')
        r = searcher.search(intent, slots)
        if r:
            context.append(r)
    elif intent == 'player_team' and 'player' in slots:
        r = searcher.search(intent, slots)
        if r:
            context.append(r)
    elif intent == 'player_performance' and 'player' in slots:
        r = searcher.search(intent, slots)
        if r:
            context.append(r)
    elif intent == 'team_region' and 'team' in slots:
        r = searcher.search(intent, slots)
        if r:
            context.append(r)
    elif intent == 'player_best_acs' or intent == 'team_best_player':
        r = searcher.search(intent, slots)
        if r:
            context.append(r)
    elif intent == 'player_events' and 'player' in slots:
        r = searcher.search(intent, slots)
        if r:
            context.append(r)

    return '\n'.join(context) if context else None


def _needs_web_search(question):
    """判断问题是否需要爬取实时数据"""
    q = question.lower()
    keywords = ['今天', '明天', '最近', '近期', '赛程', '比赛', '赛况',
                '日程', '对阵', '实时', '最新', '结果', '比分', '战况',
                '谁赢了', '谁赢了', '哪个队赢', '昨天']
    return any(k in q for k in keywords)


@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'answer': '请输入一个问题'})

    # 1. 实体识别 + 意图分类
    parsed = classifier.parse(question)

    # 2. 知识图谱上下文
    kg_context = _retrieve_kg_context(parsed)

    # 3. 实时数据（如需要）
    web_context = None
    if _needs_web_search(question):
        try:
            scraped = scraper.search(question)
            if scraped:
                web_context = scraped
        except Exception:
            pass

    # 4. 合并所有上下文
    if kg_context and web_context:
        full_context = f'【知识图谱数据】\n{kg_context}\n\n【实时赛程数据】\n{web_context}'
    elif kg_context:
        full_context = kg_context
    elif web_context:
        full_context = web_context
    else:
        full_context = None

    # 5. LLM 生成答案
    answer = llm_service.generate(question, kg_context=full_context)
    if not answer:
        answer = full_context or '抱歉，暂时无法回答，换个问题试试？'

    history.append({'question': question, 'answer': answer})
    return jsonify({'answer': answer})

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(history)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    history.clear()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

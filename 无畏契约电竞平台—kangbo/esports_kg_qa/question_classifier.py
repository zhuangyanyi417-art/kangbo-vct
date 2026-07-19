import ahocorasick
import pandas as pd


def build_entity_automaton(csv_path, alias_mapping=None):
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()

    players = df['player'].dropna().unique()
    teams = df['team'].dropna().unique()

    automaton = ahocorasick.Automaton()
    for p in players:
        automaton.add_word(p.strip().lower(), ('Player', p.strip()))
    for t in teams:
        automaton.add_word(t.strip().lower(), ('Team', t.strip()))

    if alias_mapping:
        for alias, (etype, real_name) in alias_mapping.items():
            automaton.add_word(alias.lower(), (etype, real_name))

    automaton.make_automaton()
    return automaton


class QuestionClassifier:
    def __init__(self, automaton):
        self.automaton = automaton

    def parse(self, question):
        q_lower = question.lower()
        entities = []
        for end_index, (etype, ename_original) in self.automaton.iter(q_lower):
            entities.append((etype, ename_original))

        seen = set()
        unique_entities = []
        for etype, ename in entities:
            key = (etype, ename)
            if key not in seen:
                seen.add(key)
                unique_entities.append(key)

        players = [n for t, n in unique_entities if t == 'Player']
        teams = [n for t, n in unique_entities if t == 'Team']

        intent = None
        slots = {}

        kw_team_players = ['选手', '队员', '阵容', '成员', '有哪些人', '队员名单', '介绍', '说说', '关于']
        kw_player_team = ['哪个战队', '哪个队', '在哪个队', '效力于', '属于哪个战队', '战队是', '队伍是']
        kw_performance = ['表现', '数据', '成绩', '打的', '怎么样', '发挥', '如何', '水平', 'kda', 'acs', '厉害吗', '强吗', '多少']
        kw_team_region = ['属于哪个地区', '哪个区域', '赛区', '地区', '区域']
        kw_player_events = ['参加', '比赛', '打了哪些比赛', '参与了什么赛事', '什么赛事', '哪些比赛']
        kw_best = ['最强', '最高', '最厉害', '表现最好', '谁最强', '哪个选手最强']

        if any(k in q_lower for k in kw_best):
            if teams:
                intent = 'team_best_player'
                slots['team'] = teams[0]
            else:
                intent = 'player_best_acs'
        elif teams and any(k in q_lower for k in kw_team_players):
            intent = 'team_players'
            slots['team'] = teams[0]
        elif players and any(k in q_lower for k in kw_player_team):
            intent = 'player_team'
            slots['player'] = players[0]
        elif players and any(k in q_lower for k in kw_performance):
            intent = 'player_performance'
            slots['player'] = players[0]
        elif teams and any(k in q_lower for k in kw_team_region):
            intent = 'team_region'
            slots['team'] = teams[0]
        elif players and any(k in q_lower for k in kw_player_events):
            intent = 'player_events'
            slots['player'] = players[0]

        return {
            'intent': intent,
            'slots': slots,
            'entities': {'players': players, 'teams': teams}
        }

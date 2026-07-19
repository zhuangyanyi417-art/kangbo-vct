"""从 vlr.gg 爬取 VCT 2026 完赛数据，构建完整的数据集 CSV"""
import httpx
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import re, time, os

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
OUTPUT_CSV = "/Users/luka/Documents/无畏契约电竞平台—kangbo/esports_kg_qa/data/vlr_dataset.csv"

# VCT 2026 赛事 ID 和赛区
EVENTS = [
    (2978, "VCT 2026: China Stage 2", "CN"),
    (2976, "VCT 2026: EMEA Stage 2", "EMEA"),
    (2776, "VCT 2026: Pacific Stage 2", "APAC"),
    (2977, "VCT 2026: Americas Stage 2", "NA"),
]


def get_completed_matches(event_id):
    """获取指定赛事已完成比赛的 ID 和基本信息"""
    url = f"https://www.vlr.gg/event/{event_id}"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except:
        return []
    
    soup = BeautifulSoup(r.text, "html.parser")
    matches = []
    
    for a in soup.select("a[href]"):
        href = a["href"]
        try:
            parts = href.strip("/").split("/")
            if not (len(parts) >= 2 and parts[0].isdigit() and 700000 < int(parts[0]) < 900000):
                continue
            match_id = int(parts[0])
            text = a.get_text(strip=True)
            # 检查是否为完赛比赛（包含比分，如 "2:0"）
            score_match = re.search(r'(\d+):(\d+)', text)
            if not score_match:
                continue
            score_a, score_b = int(score_match.group(1)), int(score_match.group(2))
            if score_a + score_b < 1:  # 0:0 是未开始
                continue
            matches.append({
                "match_id": match_id,
                "href": href,
            })
        except:
            continue
    
    return matches


def parse_match_data(match_id, event_name, region):
    """解析单场比赛的选手数据"""
    url = f"https://www.vlr.gg/{match_id}"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except:
        return []
    
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    
    def _last_val(raw):
        parts = [v.strip() for v in raw.split() if v.strip()]
        return parts[-1] if parts else ""
    
    def _last_kda(kda_raw):
        groups = kda_raw.split("/")
        last_group = groups[-1].strip() if groups else ""
        nums = last_group.split()
        return [int(n) if n.isdigit() else 0 for n in nums[:3]]
    
    for game in soup.select(".vm-stats-game"):
        header = game.select_one(".vm-stats-game-header")
        if not header:
            continue
        
        teams_el = header.select(".team-name")
        scores_el = header.select(".score")
        if len(teams_el) < 2 or len(scores_el) < 2:
            continue
        
        teams = [t.get_text(strip=True) for t in teams_el]
        scores = [int(s.get_text(strip=True)) for s in scores_el]
        
        # 检查是否为总计容器（只有1组数值）
        first_acs = game.select_one(".ovw-row:not(.mod-head) .ovw-cell")
        if first_acs:
            acs_raw = first_acs.get_text(separator=" ", strip=False)
            acs_count = len([v for v in acs_raw.split() if v.strip()])
            if acs_count < 2:
                continue
        
        for row in game.select(".ovw-row"):
            if "mod-head" in (row.get("class") or []):
                continue
            name_el = row.select_one(".text-of")
            player_name = name_el.get_text(strip=True) if name_el else ""
            if not player_name:
                continue
            
            cells = row.select(".ovw-cell")
            if len(cells) < 4:
                continue
            
            kda_raw = cells[3].get_text(separator=" ", strip=False)
            kda = _last_kda(kda_raw)
            kills = kda[0] if len(kda) > 0 else 0
            deaths_val = kda[1] if len(kda) > 1 else 0
            assists_val = kda[2] if len(kda) > 2 else 0
            
            acs_val = _last_val(cells[2].get_text(separator=" ", strip=False))
            rating_val = _last_val(cells[1].get_text(separator=" ", strip=False))
            kast_val = _last_val(cells[5].get_text(separator=" ", strip=False)).rstrip("%") if len(cells) > 5 else ""
            adr_val = _last_val(cells[6].get_text(separator=" ", strip=False)) if len(cells) > 6 else ""
            hs_val = _last_val(cells[7].get_text(separator=" ", strip=False)).rstrip("%") if len(cells) > 7 else ""
            fk_val = _last_val(cells[8].get_text(separator=" ", strip=False)) if len(cells) > 8 else ""
            fd_val = _last_val(cells[9].get_text(separator=" ", strip=False)) if len(cells) > 9 else ""
            
            rows.append({
                "match_id": match_id, "game_id": 0, "team": teams[0],
                "score_team": scores[0], "opponent": teams[1], "score_opp": scores[1],
                "win_lose": "team win" if scores[0] > scores[1] else "opponent win",
                "map": "N/A", "map_pick": "N/A", "player_id": 0,
                "player": player_name, "agent": "Unknown",
                "rating": rating_val, "acs": acs_val,
                "kill": kills, "death": deaths_val, "assist": assists_val,
                "kast%": kast_val, "adr": adr_val, "hs%": hs_val,
                "fk": fk_val, "fd": fd_val,
            })
    
    return rows
def build_dataset():
    """主流程：爬取所有赛事 → 爬取比赛详情 → 构建 CSV"""
    all_rows = []
    total_matches = 0
    
    for event_id, event_name, region in EVENTS:
        print(f"\n📋 正在处理: {event_name} ({region})")
        matches = get_completed_matches(event_id)
        print(f"  找到 {len(matches)} 场完赛比赛")
        
        for i, m in enumerate(matches):
            mid = m["match_id"]
            time.sleep(0.5)  # 避免请求过快
            rows = parse_match_data(mid, event_name, region)
            if rows:
                all_rows.extend(rows)
                total_matches += 1
                print(f"  [{i+1}/{len(matches)}] Match {mid}: {len(rows)} 行数据", end="\r")
            else:
                print(f"  [{i+1}/{len(matches)}] Match {mid}: 无数据")
    
    if not all_rows:
        print("\n❌ 没有爬取到任何数据")
        return
    
    # 转为 DataFrame 并排序
    df = pd.DataFrame(all_rows)
    # 按 match_id, game_id 排序
    df = df.sort_values(["match_id", "game_id", "player"]).reset_index(drop=True)
    
    # 保存 CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    
    print(f"\n\n✅ 数据集构建完成！")
    print(f"  CSV: {OUTPUT_CSV}")
    print(f"  行数: {len(df)}")
    print(f"  比赛数: {total_matches}")
    print(f"  选手数: {df['player'].nunique()}")
    print(f"  战队数: {df['team'].nunique()}")
    print(f"  列: {list(df.columns)}")


if __name__ == "__main__":
    build_dataset()

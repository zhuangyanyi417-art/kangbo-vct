"""
从 Riot Games API 构建合法数据集

使用方法:
  1. 去 https://developer.riotgames.com/ 注册获取 API Key
  2. python3 build_riot_dataset.py --key RGAPI-xxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
"""
import pandas as pd
import argparse
from datetime import datetime
from riot_api import RiotAPI, MATCH_REGIONS

VLR_CSV = "/Users/luka/Documents/无畏契约电竞平台—kangbo/esports_kg_qa/data/vlr_dataset.csv"
OUTPUT_CSV = "/Users/luka/Documents/无畏契约电竞平台—kangbo/esports_kg_qa/data/riot_dataset.csv"

# VCT 2026 Stage 2 时间范围
STAGE2_START = datetime(2026, 7, 1).timestamp() * 1000  # Riot 用毫秒
STAGE2_END = datetime(2026, 8, 31).timestamp() * 1000


def main(api_key):
    api = RiotAPI(api_key)
    
    # 从现有 CSV 获取选手列表
    df = pd.read_csv(VLR_CSV)
    known_players = set(df['player'].dropna().unique())
    
    print(f"已知选手: {len(known_players)}")
    print(f"开始通过 Riot API 查询选手 PUUID...")
    
    puuid_map = {}  # player_name → puuid
    
    # 对中国选手使用已知的 tagline（多数 VCT CN 选手 tagline=CN1）
    for i, player in enumerate(sorted(known_players)):
        print(f"  [{i+1}/{len(known_players)}] {player}...", end=" ")
        for tag in ["NA1", "EUW", "KR1", "CN1", "BR1", "LA1", "OCE"]:
            puuid = api.get_puuid(player, tag)
            if puuid:
                puuid_map[player] = (puuid, tag)
                print(f"✅ found (tag={tag})")
                break
        else:
            print("❌ not found")
    
    found = len(puuid_map)
    print(f"\n找到 {found}/{len(known_players)} 名选手的 PUUID")
    
    if found == 0:
        print("没有找到任何选手，请检查 API Key 是否正确")
        return
    
    # 对找到的选手查询比赛历史
    print(f"\n开始获取比赛数据...")
    all_matches = set()
    player_matches = {}  # puuid → [match_ids]
    
    for player, (puuid, tag) in puuid_map.items():
        for region in ["na", "eu", "kr", "ap", "br", "latam"]:
            try:
                match_ids = api.get_recent_matches(puuid, region, count=50)
                if match_ids:
                    if puuid not in player_matches:
                        player_matches[puuid] = []
                    player_matches[puuid].extend(match_ids)
                    all_matches.update(match_ids)
                    print(f"  {player} ({tag}, {region}): {len(match_ids)} 场")
            except Exception as e:
                pass
    
    print(f"\n共找到 {len(all_matches)} 场比赛")
    
    # 获取比赛详情
    print(f"\n获取比赛详情...")
    all_rows = []
    
    for i, match_id in enumerate(sorted(all_matches)[:200]):  # 最多 200 场
        print(f"  [{i+1}/{min(len(all_matches), 200)}] {match_id[:12]}...", end=" ")
        try:
            data = api.get_match_details(match_id)
            rows = api.parse_match(data)
            if rows:
                all_rows.extend(rows)
                print(f"{len(rows)} 行")
            else:
                print("空")
        except Exception as e:
            print(f"错误: {e}")
    
    if not all_rows:
        print("\n❌ 没有爬取到任何数据")
        return
    
    # 保存
    df_out = pd.DataFrame(all_rows)
    df_out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    
    print(f"\n✅ Riot 数据集构建完成！")
    print(f"  文件: {OUTPUT_CSV}")
    print(f"  行数: {len(df_out)}")
    print(f"  比赛数: {df_out['match_id'].nunique()}")
    print(f"  选手数: {df_out['player'].nunique()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True, help="Riot Games API Key")
    args = parser.parse_args()
    main(args.key)

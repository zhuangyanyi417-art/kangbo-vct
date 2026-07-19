"""VCT 赛事信息爬虫 - 从 vlr.gg 获取实时比赛数据"""
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

# 赛区缩写映射
REGION_NAMES = {
    "VCT 2026: China Stage 2": "CN赛区",
    "VCT 2026: Pacific Stage 2": "太平洋赛区",
    "VCT 2026: EMEA Stage 2": "EMEA赛区",
    "VCT 2026: Americas Stage 2": "美洲赛区",
    "VCT 2026: Game Changers": "Game Changers",
}


def parse_match_time(time_str, date_str=None):
    """解析 vlr.gg 的时间格式"""
    try:
        now = datetime.now(timezone(timedelta(hours=8)))
        time_str = time_str.strip()

        # "Today 2:00 AM" / "Tomorrow 8:00 PM"
        if "today" in time_str.lower():
            parts = time_str.lower().replace("today", "").strip()
            t = datetime.strptime(parts, "%I:%M %p").time()
            return now.replace(hour=t.hour, minute=t.minute, second=0)
        elif "tomorrow" in time_str.lower():
            parts = time_str.lower().replace("tomorrow", "").strip()
            t = datetime.strptime(parts, "%I:%M %p").time()
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=t.hour, minute=t.minute, second=0)
        else:
            # Just a time like "2:00 AM"
            t = datetime.strptime(time_str.strip(), "%I:%M %p").time()
            return now.replace(hour=t.hour, minute=t.minute, second=0)
    except:
        return None


def extract_team_name(team_div):
    """从 team div 里提取战队名"""
    text_of = team_div.select_one(".text-of")
    if text_of:
        # Remove flag span text
        for span in text_of.select("span"):
            span.decompose()
        return text_of.get_text(strip=True)
    return ""


def fetch_matches():
    """爬取 vlr.gg/matches 获取比赛日程"""
    try:
        r = httpx.get("https://www.vlr.gg/matches", headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return f"爬取比赛数据失败：{e}"

    soup = BeautifulSoup(r.text, "html.parser")
    match_items = soup.select("a.wf-module-item.match-item")

    results = {"upcoming": [], "live": [], "recent": [], "today": []}
    now = datetime.now(timezone(timedelta(hours=8)))
    today_str = now.strftime("%Y-%m-%d")

    for item in match_items:
        try:
            # 时间
            time_el = item.select_one(".match-item-time")
            time_text = time_el.get_text(strip=True) if time_el else ""

            # 战队
            team_divs = item.select(".match-item-vs-team")
            teams = [extract_team_name(td) for td in team_divs]

            # 比分
            scores = []
            for td in team_divs:
                score_el = td.select_one(".match-item-vs-team-score")
                scores.append(score_el.get_text(strip=True) if score_el else "-")

            # 比赛状态
            eta_el = item.select_one(".match-item-eta .ml-status")
            status = eta_el.get_text(strip=True) if eta_el else ""

            # 赛事名称
            event_el = item.select_one(".match-item-event")
            event_name = event_el.get_text(strip=True) if event_el else ""

            # 系列赛
            series_el = item.select_one(".match-item-event-series")
            series = series_el.get_text(strip=True) if series_el else ""

            # 比赛链接
            href = item.get("href", "")

            match_info = {
                "teams": teams,
                "scores": scores,
                "time": time_text,
                "status": status,
                "event": event_name,
                "series": series,
                "url": f"https://www.vlr.gg{href}",
            }

            if status.lower() == "live":
                results["live"].append(match_info)
            elif status.lower() == "upcoming":
                results["upcoming"].append(match_info)
            else:
                results["recent"].append(match_info)

            # 判断是否今天
            match_time = parse_match_time(time_text)
            if match_time and match_time.strftime("%Y-%m-%d") == today_str:
                results["today"].append(match_info)
            elif not match_time and not results["today"]:
                # 无法判断时间的放到最近
                pass

        except Exception:
            continue

    return format_results(results)


def format_results(results):
    """将爬取结果格式化成文本"""
    lines = []
    lines.append("📅 VLR.gg 实时比赛数据")
    lines.append("=" * 50)

    if results["live"]:
        lines.append("\n🔴 正在进行的比赛：")
        for m in results["live"]:
            teams = " vs ".join(m["teams"]) if m["teams"] else "?"
            scores = " : ".join(m["scores"]) if m["scores"] else "-"
            lines.append(f"  {teams}  [{scores}]")
            if m["event"]:
                lines.append(f"    赛事：{m['event']}")

    if results["today"]:
        lines.append(f"\n📌 今天的比赛：")
        for m in results["today"]:
            teams = " vs ".join(m["teams"]) if m["teams"] else "?"
            et = m.get("eta", m["time"])
            lines.append(f"  ⏰ {m['time']}  {teams}")
            if m["event"]:
                lines.append(f"    赛事：{m['event']}")
            if m["series"]:
                lines.append(f"    阶段：{m['series']}")

    if results["upcoming"]:
        lines.append(f"\n⏳ 即将进行的比赛（共 {len(results['upcoming'])} 场）：")
        for m in results["upcoming"][:10]:  # 最多显示 10 场
            teams = " vs ".join(m["teams"]) if m["teams"] else "?"
            lines.append(f"  {m['time']}  {teams}")
            if m["event"]:
                lines.append(f"    赛事：{m['event']}")
            if m["series"]:
                lines.append(f"    阶段：{m['series']}")
        if len(results["upcoming"]) > 10:
            lines.append(f"  ...还有 {len(results['upcoming']) - 10} 场")

    if results["recent"]:
        lines.append(f"\n✅ 最近结束的比赛（共 {len(results['recent'])} 场）：")
        for m in results["recent"][:5]:
            teams = " vs ".join(m["teams"]) if m["teams"] else "?"
            scores = " : ".join(m["scores"]) if m["scores"] else "-"
            lines.append(f"  {teams}  [{scores}]")
            if m["event"]:
                lines.append(f"    赛事：{m['event']}")

    return "\n".join(lines)


def search_team(team_name):
    """搜索特定战队的数据"""
    try:
        # 先爬比赛页，找包含该战队的比赛
        matches_text = fetch_matches()
        if not matches_text:
            return None

        # 简单搜索：在比赛数据中找战队名
        team_lower = team_name.lower()
        lines = matches_text.split("\n")
        relevant = [l for l in lines if team_lower in l.lower()]

        if relevant:
            return f"在 vlr.gg 上找到关于 {team_name} 的信息：\n" + "\n".join(relevant[:10])
        return None
    except Exception as e:
        return None


def search(query):
    """通用搜索入口 - 根据查询决定爬什么"""
    q = query.lower()

    if any(kw in q for kw in ["比赛", "赛程", "日程", "赛况", "今天", "最近", "近期"]):
        return fetch_matches()

    # 搜特定战队
    teams = ["edg", "fpx", "drx", "fnc", "fnatic", "t1", "prx", "sen",
             "loud", "navi", "kc", "tl", "vit", "th", "lev", "100t",
             "c9", "nrg", "eg", "blg", "te", "fut", "bb", "bb", "mibr",
             "fur", "kru", "ge", "ts", "rrq", "tln", "dfm", "spb", "bny",
             "zeta", "geng", "gen", "gia", "koi", "fpx", "ase"]
    for team in teams:
        if team in q:
            return fetch_matches()  # 目前先返回全部赛程，以后可以细化

    return None


if __name__ == "__main__":
    print(fetch_matches())

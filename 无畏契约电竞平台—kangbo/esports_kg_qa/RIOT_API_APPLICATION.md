# Riot Games API Production Key 申请文案

## 前往 https://developer.riotgames.com/apply 填写

---

### Application Name（应用名称）

**VCT Analytics — 无畏契约电竞赛事数据平台**

---

### Application Description（应用描述）

**英文版（直接复制）：**

> VCT Analytics is a comprehensive Valorant esports data platform that provides real-time match statistics, player performance rankings, tournament schedules, and AI-powered analytics for VCT (Valorant Champions Tour) events. 
>
> The platform serves Chinese-speaking Valorant fans by aggregating official match data across all VCT leagues (CN, EMEA, Americas, Pacific), presenting it through an intuitive dashboard with features including:
> - Real-time match schedules and results
> - Player performance rankings (ACS, KDA, ADR, etc.)
> - Team and player statistics comparison
> - AI-assisted Q&A system for match data queries
> - Event-based data filtering (Kickoff, Stage 1, Stage 2, Masters, Champions)
>
> We use Riot's official API as the sole data source for match statistics, player performance data, and match history. All data is displayed with proper attribution to Riot Games. The platform does NOT modify, redistribute, or sell Riot's data — it simply presents it in a more accessible and analytical format for fans.
>
> The platform directly benefits the Valorant esports ecosystem by increasing fan engagement and making tournament data more accessible, especially for the Chinese-speaking audience.

**中文版（供参考）：**

> VCT Analytics 是一个全面的无畏契约电竞赛事数据平台，为 VCT（Valorant Champions Tour）赛事提供实时比赛数据、选手表现排行、赛程日历和 AI 智能分析功能。
>
> 平台面向中文 Valorant 玩家群体，整合所有 VCT 赛区（CN、EMEA、Americas、Pacific）的官方赛事数据，通过可视化仪表盘呈现，核心功能包括：
> - 实时赛程和比赛结果
> - 选手表现排行榜（ACS、KDA、ADR 等指标）
> - 战队和选手数据对比
> - AI 智能问答系统
> - 按赛事阶段筛选（启点赛、Stage 1、Stage 2、大师赛、冠军赛）
>
> 我们使用 Riot 官方 API 作为比赛数据和选手表现的唯一数据源。所有数据均标注 Riot Games 版权信息。平台不对 Riot 的数据进行修改、转售或分发，仅以更易读、更分析化的形式呈现给粉丝。
>
> 该平台直接提升了 Valorant 电竞生态的粉丝参与度，尤其为中文观众群体提供了更便捷的赛事数据访问方式。

---

### Requested APIs（申请的 API）

勾选以下所有适用的：

- [x] **VAL-Match** — 比赛数据（核心需求）
- [x] **VAL-Status** — 服务器状态
- [x] **VAL-Content** — 游戏内容（英雄、地图等）
- [x] **Account** — 选手账号查询

---

### Why do you need Production API Key?（为什么需要 Production Key？）

> We are building a commercial esports data platform targeting the Chinese-speaking Valorant community. Our Development API Key expires every 24 hours, which is not sustainable for a production service that requires continuous data updates. A Production API Key is essential for:
>
> 1. **Data freshness**: We need to update match results and player statistics in real-time as VCT matches conclude
> 2. **Service reliability**: Daily key regeneration would cause service interruptions and poor user experience
> 3. **Scale requirements**: Our platform needs to handle regular API calls to serve match data, player rankings, and historical statistics for tens of thousands of users
>
> We fully comply with Riot's Developer Terms of Service and will include proper attribution to Riot Games for all data displayed.

---

### Estimated User Base（预估用户规模）

**Monthly Active Users（月活）：**

- First 3 months: 5,000 - 10,000 MAU
- 6 months: 30,000 - 50,000 MAU
- 12 months: 100,000 - 300,000 MAU

**Daily API Calls（日 API 调用量）：**

- Match data queries: ~10,000 - 30,000 calls/day
- Player account lookups: ~3,000 - 10,000 calls/day
- Total estimated: ~15,000 - 50,000 calls/day

---

### How do you plan to use Riot's data?（数据使用计划）

> Our platform uses Riot's API data in the following ways:
>
> 1. **Match Results**: Display VCT match scores, team compositions, and map details
> 2. **Player Statistics**: Show per-player and per-match performance data including ACS, KDA, ADR, headshot percentage, etc.
> 3. **Player Rankings**: Aggregate and rank players by various performance metrics
> 4. **Historical Data**: Maintain a database of past matches for trend analysis and comparison
>
> **Data Handling Policies:**
> - All data is served read-only to end users
> - Data is cached to minimize API calls (typically 5-15 minute cache)
> - No data is sold, sublicensed, or redistributed to third parties
> - All match and player data is clearly attributed: "Data sourced from Riot Games"
> - We use only official Riot API endpoints — no scraping, no reverse engineering
> - User data (PUUID, account info) is not stored or tracked beyond what's needed for match lookups

---

### Terms of Service Acknowledgment（服务条款确认）

确保勾选：

- [x] I have read and agree to the **Riot Games Developer Terms of Service**
- [x] I understand that **data must be attributed to Riot Games**
- [x] I understand that I **cannot sell or sublicense Riot's data**
- [x] My application **benefits the Valorant/Riot Games community**

---

## 审核通过后的接入

Riot 通过后会发一封邮件，Production Key 长这样：

```
RGAPI-PROD-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

拿到之后按以下步骤接入系统：

```bash
# 1. 保存 key
echo "RIOT_API_KEY=RGAPI-PROD-xxxxxxxx" > .env

# 2. 运行迁移脚本（增量模式）
python3 build_riot_dataset.py --key $RIOT_API_KEY

# 3. 重建知识图谱
python3 build_kg.py
```

之后系统修改 `app.py` 里的数据源配置，增加 `.env` 环境变量读取：

```python
import os
CSV_PATH = os.getenv("CSV_PATH", "data/riot_dataset.csv")
RIOT_API_KEY = os.getenv("RIOT_API_KEY", "")

# 如果 Production Key 存在，用它定期更新数据
if RIOT_API_KEY:
    from build_riot_dataset import update_dataset
    update_dataset(RIOT_API_KEY)
```

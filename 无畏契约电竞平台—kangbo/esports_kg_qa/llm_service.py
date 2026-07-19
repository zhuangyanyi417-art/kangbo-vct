from datetime import datetime
from openai import OpenAI

API_KEY = "sk-d90451887e944e2a93ebabe0ec5b9a27"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=60)


def generate(question, kg_context=None):
    today = datetime.now().strftime("%Y年%m月%d日")

    system = (
        f"你是全能AI助手，今天是 {today}。"
        "你擅长回答各种问题，包括但不限于电竞、科技、生活等。\n"
        "额外能力：你可以访问无畏契约（Valorant）VCT赛事知识图谱，"
        "当用户提到战队或选手时，你会获得相关数据。\n"
        "回答风格：自然、口语化、有温度，不要像机器人一样刻板。\n"
        "不要自我设限——你有完整的世界知识，什么都能聊。"
    )

    messages = [{"role": "system", "content": system}]

    if kg_context:
        messages.append({
            "role": "system",
            "content": f"知识图谱查询结果（供参考）：\n{kg_context}"
        })

    messages.append({"role": "user", "content": question})

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.8,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return None  # 返回 None 让上层降级

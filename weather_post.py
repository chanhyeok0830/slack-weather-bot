import os
import requests
import random
from datetime import datetime, timezone, timedelta

# ─── 1. 이모티콘 매핑 ─────────────────────────────────────────────────────────
EMOJI_MAP = {
    "맑음": "🌞",
    "구름": "☁️",
    "흐림": "☁️",
    "비": "☔",
    "눈": "❄️",
    "폭풍": "⛈️",
}

# ─── 2. 날씨별 자연어 템플릿 ───────────────────────────────────────────────────
TEMPLATES = {
    "맑음": [
        "오늘은 하루 종일 맑은 날씨가 예상돼요. ☀️",
        "하늘이 맑고 화창해요. 야외 활동하기 좋아요!",
    ],
    "구름": [
        "구름이 약간 끼겠지만 대체로 맑아요. ☁️",
        "오늘은 흐리지만 큰 비 없이 온화할 예정이에요.",
    ],
    "흐림": [
        "오늘은 전반적으로 흐린 날씨가 이어질 거예요.",
        "구름이 많아 해가 잘 보이지 않을 수 있어요.",
    ],
    "비": [
        "약한 비가 내릴 수 있으니 우산 챙기세요. ☔",
        "비 소식이 있어요. 외출하실 때 우산 잊지 마세요!",
    ],
    "눈": [
        "눈 소식이 있어요. 따뜻하게 입으세요! ❄️",
        "눈이 올 수 있으니 주의하세요.",
    ],
    "폭풍": [
        "천둥과 번개를 동반한 비가 예상돼요. 주의하세요! ⛈️",
    ],
}
    
def select_emoji(desc):
    for key, emo in EMOJI_MAP.items():
        if key in desc:
            return emo
    return "🌈"

def select_template(desc):
    for key, tpl_list in TEMPLATES.items():
        if key in desc:
            return random.choice(tpl_list)
    # 기본 템플릿
    return f"{desc} 날씨입니다."

# ─── 3. 날씨 가져오기 ─────────────────────────────────────────────────────────
def fetch_weather():
    LAT, LON = 37.8813, 127.7299
    today = datetime.now(timezone(timedelta(hours=9))).date()

    # 현재 날씨
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}&lon={LON}"
        f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
        "&units=metric"
        "&lang=kr"
    )
    r = requests.get(url); r.raise_for_status()
    data = r.json()

    return {
        "date": today.strftime("%m월 %d일"),
        "desc": data["weather"][0]["description"],
        "temp": data["main"]["temp"],
        "feels": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        # POP는 forecast에서 뽑아오거나 대체로 0으로 설정
        "pop": 0,
    }

# ─── 4. 슬랙 전송 ────────────────────────────────────────────────────────────
def post_to_slack(info):
    emoji     = select_emoji(info["desc"])
    sentence  = select_template(info["desc"])
    # 메시지 문장 구성: 이모지는 문장 안·끝·별도 줄로 자유 배치
    text_lines = [
        f"{emoji}",  # 별도 줄에 이모티콘만
        f"*오늘의 날씨* ({info['date']})",
        f"> {sentence}",
        f"> 기온: {info['temp']:.1f}°C  (체감: {info['feels']:.1f}°C)",
        f"> 습도: {info['humidity']}%",
        f"> 강수확률: {info['pop']:.0f}%"
    ]
    text = "\n".join(text_lines)

    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"},
        json={
            "channel": os.getenv("SLACK_CHANNEL_ID"),
            "text": text,
            "mrkdwn": True,
            "icon_emoji": emoji,        # 프로필 옆 이모티콘
            # "username": "오늘의 날씨 봇"
        }
    )
    resp.raise_for_status()

def main():
    info = fetch_weather()
    post_to_slack(info)

if __name__ == "__main__":
    main()

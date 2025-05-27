import os
import requests
from datetime import datetime, timezone, timedelta

# ─── 1. 환경 변수 디버깅 ─────────────────────────────────────────────────────────
def debug_env():
    print("=== ENVIRONMENT VARIABLES ===")
    print(f"OPENWEATHER_API_KEY loaded: {'YES' if os.getenv('OPENWEATHER_API_KEY') else 'NO'}")
    print(f"SLACK_BOT_TOKEN       loaded: {'YES' if os.getenv('SLACK_BOT_TOKEN') else 'NO'}")
    print(f"SLACK_CHANNEL_ID      loaded: {'YES' if os.getenv('SLACK_CHANNEL_ID') else 'NO'}")
    print("=============================\n")

# ─── 2. 이모티콘 매핑 ────────────────────────────────────────────────────────────
EMOJI_MAP = {
    "맑음": "🌞",
    "구름": "☁️",
    "흐림": "🌥️",
    "비": "☔",
    "눈": "❄️",
    "폭풍": "⛈️",
}

def select_emoji(description):
    for key, emoji in EMOJI_MAP.items():
        if key in description:
            return emoji
    return "🌈"  # 기타 날씨

# ─── 3. 오늘 날씨 가져오기 ────────────────────────────────────────────────────
def fetch_today_weather():
    LAT, LON = 37.8813, 127.7299
    today = datetime.now(timezone(timedelta(hours=9))).date()

    # 3.1 현재 날씨 (한국어)
    url_cur = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}&lon={LON}"
        f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
        "&units=metric"
        "&lang=kr"
    )
    r1 = requests.get(url_cur); r1.raise_for_status()
    cur = r1.json()

    # 3.2 5일 Forecast에서 오늘 강수확률(pop) 최대값 추출
    url_fc = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={LAT}&lon={LON}"
        f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
        "&units=metric"
        "&lang=kr"
    )
    r2 = requests.get(url_fc); r2.raise_for_status()
    fc = r2.json()

    pops = []
    for item in fc.get("list", []):
        dt = datetime.fromtimestamp(item["dt"], timezone(timedelta(hours=9)))
        if dt.date() == today:
            pops.append(item.get("pop", 0))

    pop_max = max(pops) * 100 if pops else 0

    return {
        "date_str": today.strftime("%m월 %d일"),
        "description": cur["weather"][0]["description"],  # 한국어 설명
        "temp": cur["main"]["temp"],
        "feels_like": cur["main"]["feels_like"],
        "humidity": cur["main"]["humidity"],
        "pop": pop_max,
    }

# ─── 4. 슬랙에 전송 ───────────────────────────────────────────────────────────
def post_to_slack(info):
    emoji = select_emoji(info["description"])
    lines = [
        f"*오늘의 날씨* ({info['date_str']}) {emoji}",
        f"> 날씨: {info['description']}",
        f"> 기온: {info['temp']:.1f}°C  (체감: {info['feels_like']:.1f}°C)",
        f"> 습도: {info['humidity']}%",
        f"> 강수확률: {info['pop']:.0f}%"
    ]
    text = "\n".join(lines)

    slack_url = "https://slack.com/api/chat.postMessage"
    headers   = {"Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"}
    payload   = {
        "channel": os.getenv("SLACK_CHANNEL_ID"),
        "text": text,
        "mrkdwn": True,
        "icon_emoji": emoji,  # 메시지 사이드 아이콘
        # "username": "오늘의 날씨 봇"  # 원하면 봇 이름도 바꿀 수 있음
    }

    resp = requests.post(slack_url, json=payload, headers=headers)
    resp.raise_for_status()

# ─── 5. 메인 실행 ─────────────────────────────────────────────────────────────
def main():
    debug_env()
    try:
        info = fetch_today_weather()
    except Exception as e:
        print(f"[ERROR] fetch_today_weather(): {e}")
        return

    try:
        post_to_slack(info)
    except Exception as e:
        print(f"[ERROR] post_to_slack(): {e}")
        return

    print("[Main] Done.")

if __name__ == "__main__":
    main()

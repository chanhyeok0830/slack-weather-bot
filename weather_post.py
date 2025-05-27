import os
import requests
from datetime import datetime, timezone, timedelta

def debug_env():
    print("=== ENVIRONMENT VARIABLES ===")
    print(f"OPENWEATHER_API_KEY loaded: {'YES' if os.getenv('OPENWEATHER_API_KEY') else 'NO'}")
    print(f"SLACK_BOT_TOKEN   loaded: {'YES' if os.getenv('SLACK_BOT_TOKEN') else 'NO'}")
    print(f"SLACK_CHANNEL_ID  loaded: {'YES' if os.getenv('SLACK_CHANNEL_ID') else 'NO'}")
    print("=============================\n")

def fetch_today_weather():
    LAT, LON = 37.8813, 127.7299
    today = datetime.now(timezone(timedelta(hours=9))).date()

    # 1) Current Weather (한국어)
    url_cur = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}&lon={LON}"
        f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
        "&units=metric"
        "&lang=kr"
    )
    r1 = requests.get(url_cur); r1.raise_for_status()
    cur = r1.json()

    # 2) 5일 Forecast에서 오늘 날짜에 해당하는 pop(강수확률)만 뽑기
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

    pop_max = max(pops)*100 if pops else 0

    return {
        "date_str": today,
        "weather": cur["weather"][0]["description"],  # 한국어
        "temp": cur["main"]["temp"],
        "feels_like": cur["main"]["feels_like"],
        "humidity": cur["main"]["humidity"],
        "pop": pop_max,
    }

def post_to_slack(info):
    lines = [
        f"*오늘의 날씨* ({info['date_str']})",
        f"> 날씨: {info['weather']}",
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
        "mrkdwn": True
    }

    resp = requests.post(slack_url, json=payload, headers=headers)
    resp.raise_for_status()

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

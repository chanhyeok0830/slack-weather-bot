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
    # 춘천 좌표
    LAT, LON = 37.8813, 127.7299

    # 오늘 날짜 문자열
    today = datetime.now(timezone(timedelta(hours=9))).date()

    # Current Weather API 호출
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}&lon={LON}"
        f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
        f"&units=metric"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    return {
        "date_str": today,
        "weather": data["weather"][0]["description"],  # ex: broken clouds
        "temp": data["main"]["temp"],                  # 현재 온도
        "feels_like": data["main"]["feels_like"],      # 체감 온도
        "humidity": data["main"]["humidity"],          # 습도
    }

def post_to_slack(info):
    lines = [
        f"*오늘의 날씨* ({info['date_str']})",
        f"> 날씨: {info['weather']}",
        f"> 기온: {info['temp']:.1f}°C  (체감: {info['feels_like']:.1f}°C)",
        f"> 습도: {info['humidity']}%"
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
